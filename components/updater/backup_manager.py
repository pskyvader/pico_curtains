from components.file_manager import FileManager
import os
from lib.logging import getLogger, handlers


class BackupManager(FileManager):
    log_file = "backupmanager.txt"

    def __init__(self, main_dir, new_version_dir, backup_dir):
        super().__init__(main_dir, new_version_dir, backup_dir)
        self.logger = getLogger("backupmanager")
        self.logger.addHandler(handlers.RotatingFileHandler(self.log_file))

    def create_backup(self):
        self.logger.debug(
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
        self.logger.debug(
            "Backup created at {} ...".format(self.backup_dir),
        )
        return True

    def restore_backup(self):
        self.logger.debug(
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
        self.logger.debug("Backup restored at {} ...".format(self.main_dir))
        return True

    def delete_old_version(self):
        self.logger.debug(
            "Deleting old version at {} ...".format(self.main_dir),
        )
        self._rmtree(
            self.main_dir,
            preserve=[self.main_dir, self.backup_dir, self.new_version_dir],
        )
        self.logger.debug(
            "Deleted old version at {} ...".format(self.main_dir),
        )
        return True

    def install_new_version(self):
        self.logger.debug(
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
        self.logger.info(
            "Update installed, please reboot now",
        )
        return True
