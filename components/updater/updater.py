from components.esp.web_client import web_client
from components.connection_manager import connect_process
from components.updater.version_manager import get_version
from components.updater.backup_manager import BackupManager

from lib.logging import getLogger, handlers, StreamHandler
import gc


class updater:
    version_file = "version.json"
    log_file = "updater_log.txt"

    def __init__(
        self, wifi_ssid, wifi_pass, update_url, update_port=80, uart_tx=4, uart_rx=5
    ) -> None:
        self.update_url = update_url
        self.update_port = update_port
        self.esp_process = web_client(
            wifi_ssid=wifi_ssid, wifi_pass=wifi_pass, uart_tx=uart_tx, uart_rx=uart_rx
        )
        self.backup_manager = BackupManager(
            main_dir="", backup_dir="backup", new_version_dir="new"
        )
        self.logger_updater = getLogger("updater")
        self.logger_updater.addHandler(handlers.RotatingFileHandler(self.log_file))
        self.logger_updater.addHandler(StreamHandler())

    def _download_all_files(self, files_list):
        self.backup_manager.create_new_version(files_list)
        for file_url in files_list:
            gc.collect()
            self.logger_updater.info(f"free memory: {gc.mem_free()}")
            self.logger_updater.info(f"downloading file: {file_url}")
            file_path = self.backup_manager.new_version_dir + "/" + file_url

            (header, body, status_code) = self.esp_process.get_url_response(
                self.update_url + file_url, port=self.update_port
            )
            if status_code != 200:
                self.logger_updater.error(f"Failed to download file: {file_url}")
                return False
            try:
                with open(file_path, "wb") as file_object:
                    self.logger_updater.debug(f"file {file_path} open")
                    file_content = body
                    file_object.write(file_content)
            except OSError as e:
                self.logger_updater.error(
                    f"Failed to write file {file_url}->{file_path}:" + str(e)
                )
                return False
            except Exception as e:
                print(f"An error occurred: {e}")
        return True

    def update_process(self, files_list):
        self.logger_updater.info("Update found. Updating new version...")
        if not self.backup_manager.create_backup():
            self.logger_updater.error("Backup failed, aborting")
            return False

        try:
            if not self._download_all_files(files_list):
                self.logger_updater.error("Failed to download update, rolling back")
                if self.backup_manager.restore_backup():
                    self.logger_updater.info("Rolled back. booting old version...")
                    return False
                self.logger_updater.critical(
                    "Rolled back failed, RUUUUN B1TCH, RUUUUN!!!!"
                )
                return False
            # self.backup_manager.delete_old_version()
            self.backup_manager.install_new_version()
            self.backup_manager.delete_backup()
            # If everything goes well, return True
            self.logger_updater.info("Update process completed successfully")
            return True
        except Exception as e:
            self.logger_updater.error(f"Failed to update process: {e}")
            return False

    def start_update(self):
        connect_process(self.esp_process)
        if not self.esp_process.is_initialized():
            self.logger_updater.error("No connection, update aborted.")
            return False

        url = self.update_url
        port = self.update_port
        (header, body, status_code) = self.esp_process.get_url_response(url, port)
        if body == None:
            self.logger_updater.error("No body found")
            return False
        if not get_version(
            self.esp_process,
            self.update_url,
            self.update_port,
            self.version_file,
            body,
        ):
            self.logger_updater.info(
                "No update found. Already updated to the last version"
            )
            return False
        if not self.update_process(body):
            return False

        self.logger_updater.info("Update succeded. booting new version...")
        return True
