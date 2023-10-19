from components.file_manager import FileManager
import os
from lib.logging import getLogger, handlers, StreamHandler


class BackupManager(FileManager):
    log_file = "backupmanager.txt"

    def __init__(self, main_dir, new_version_dir, backup_dir):
        super().__init__(main_dir, new_version_dir, backup_dir)
        self.logger_backup_manager = getLogger("backupmanager")
        self.logger_backup_manager.addHandler(
            handlers.RotatingFileHandler(self.log_file)
        )
        self.logger_backup_manager.addHandler(StreamHandler())

    def create_backup(self):
        self.logger_backup_manager.debug(
            "creating backup {} -> {}...".format(self.main_dir, self.backup_dir),
        )
        if self.supports_rename:
            os.rename(self.main_dir, self.backup_dir)
        else:
            if not self._exists_dir(self.backup_dir):
                self._mk_dirs(self.backup_dir)
            self._copy_directory(
                self.main_dir,
                self.backup_dir,
                exclude=[self.backup_dir, self.new_version_dir],
            )
            self._rmtree(self.main_dir, preserve=[self.main_dir, self.backup_dir])
        self.logger_backup_manager.debug(
            "Backup created at {} ...".format(self.backup_dir),
        )
        return True

    def restore_backup(self):
        self.logger_backup_manager.debug(
            "restoring backup  {} -> {}...".format(self.backup_dir, self.main_dir)
        )
        if self.supports_rename:
            os.rename(self.backup_dir, self.main_dir)
        else:
            self._copy_directory(
                self.backup_dir,
                self.main_dir,
                exclude=[self.main_dir, self.new_version_dir],
            )
            self._rmtree(self.backup_dir, preserve=[self.main_dir])
        self.logger_backup_manager.debug(
            "Backup restored at {} ...".format(self.main_dir)
        )
        return True

    def delete_old_version(self):
        self.logger_backup_manager.debug(
            "Deleting old version at {} ...".format(self.main_dir),
        )
        self._rmtree(
            self.main_dir,
            preserve=[self.main_dir, self.backup_dir, self.new_version_dir],
        )
        self.logger_backup_manager.debug(
            "Deleted old version at {} ...".format(self.main_dir),
        )
        return True

    def create_new_version(self, files_list):
        self.logger_backup_manager.debug(
            "creating new version at  {} ...".format(self.new_version_dir)
        )

        if self._exists_dir(self.new_version_dir):
            self._rmtree(self.new_version_dir)

        directories_list = []
        for file_url in files_list:
            file_path = self.new_version_dir + "/" + file_url
            paths = "/".join((file_path.split("/"))[:-1])
            directories_list.append(paths)
        directories_list = set(directories_list)
        for directory in directories_list:
            self._mk_dirs(directory)

    def install_new_version(self):
        self.logger_backup_manager.debug(
            "Installing new version at  {} -> {}...".format(
                self.new_version_dir, self.main_dir
            )
        )
        if self.supports_rename:
            os.rename(self.new_version_dir, self.main_dir)
        else:
            if not self._exists_dir(self.new_version_dir):
                self._mk_dirs(self.new_version_dir)
            self._copy_directory(
                self.new_version_dir,
                self.main_dir,
                exclude=[self.new_version_dir, self.backup_dir],
            )
            self._rmtree(
                self.new_version_dir, preserve=[self.main_dir, self.backup_dir]
            )
        self.logger_backup_manager.info(
            "Update installed, please reboot now",
        )
        return True
