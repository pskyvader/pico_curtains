from components.esp.web_client import web_client
from components.logger import log_message

print("A")
from components.updater.connection_manager import connect_process

print("b")
from components.updater.file_manager import get_version
from components.updater.backup_manager import create_backup, rollback
import uos


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

    def update_process(self, files_list):
        try:
            for file_url in files_list:
                # Download the file from the specified URL
                (header, body, status_code) = self.esp_process.get_url_response(
                    file_url
                )

                # Check if the download was successful (status code 200)
                if status_code != 200:
                    log_message(f"Failed to download file: {file_url}", self.log_file)
                    return False

                # Extract the route (folder/file path) from the URL
                route = file_url.split("/", 3)[-1]

                # Create any necessary subdirectories
                folder_path = uos.path.dirname(route)
                if folder_path:
                    uos.makedirs(folder_path, exist_ok=True)

                # Write the downloaded file contents to the appropriate file
                with open(route, "wb") as f:
                    f.write(body)

            # If everything goes well, return True
            log_message("Update process completed successfully", self.log_file)
            return True
        except Exception as e:
            log_message(f"Failed to update process: {e}", self.log_file)
            return False

    def start_update(self):
        connect_process(
            self.esp_process,
            self.log_file,
        )

        if not self.esp_process.is_initialized():
            log_message("No connection, update aborted.", self.log_file)
            return False

        url = self.update_url
        port = self.update_port
        (header, body, status_code) = self.esp_process.get_url_response(url, port)
        if body == None:
            log_message("No body found", self.log_file)
            return False
        if not get_version(
            self.esp_process,
            self.update_url,
            self.update_port,
            self.version_file,
            self.log_file,
            body,
        ):
            log_message(
                "No update found. Already updated to the last version",
                self.log_file,
            )
            return False
        log_message("Update found. Updating new version...", self.log_file)
        if not create_backup(self.log_file):
            log_message("Backup failed, aborting", self.log_file)
            return False

        if not self.update_process(body):
            log_message("Update fail, rolling back", self.log_file)
            if rollback(self.log_file):
                log_message("Rolled back. booting old version...", self.log_file)
                return False
            log_message("Rolled back failed, RUUUUN B1TCH, RUUUUN!!!!", self.log_file)
            return False
        log_message("Update succeded. booting new version...", self.log_file)
        return True
