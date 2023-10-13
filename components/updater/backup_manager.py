from components.logger import log_message
import uos


def create_backup(log_file, backup_directory="/backup"):
    # try:
    entries = uos.listdir()
    if backup_directory in entries:
        _remove_directory(backup_directory)
    uos.mkdir(backup_directory)
    log_message("2", log_file)

    log_message(str(uos.ilistdir("/")), log_file)
    # Copy every file, subfolder, and files in those subfolders from the root "/" to the backup directory
    for root, dirs, files in uos.ilistdir("/"):
        log_message("3", log_file)
        for entry in dirs + files:
            log_message("4", log_file)
            # Get the absolute path of the file or subdirectory
            entry_path = root + "/" + entry

            # Get the corresponding path within the backup directory
            backup_path = backup_directory + "/" + entry_path[1:]

            # Create the necessary directories in the backup directory if they don't exist
            _makedirs(backup_path)

            # Copy the file or subdirectory to the backup directory
            if entry[0] == 0x4000:  # Directory flag
                _mkdir(backup_path)
            else:
                _copy_file(entry_path, backup_path)
    log_message("5", log_file)

    # If everything goes well, return True
    log_message("Backup created successfully", log_file)
    return True


# except Exception as e:
#     log_message("Failed to create backup: {}".format(e), log_file)
#     return False


def _remove_directory(directory):
    for root, dirs, files in uos.ilistdir(directory):
        for entry in dirs + files:
            entry_path = uos.path.join(root, entry)
            if entry[0] == 0x4000:  # Directory flag
                _remove_directory(entry_path)
            else:
                uos.remove(entry_path)
    uos.rmdir(directory)


def _makedirs(directory):
    if not uos.path.exists(directory):
        parent = uos.path.dirname(directory)
        if parent and not uos.path.exists(parent):
            _makedirs(parent)
        uos.mkdir(directory)


def _mkdir(directory):
    if not uos.path.exists(directory):
        uos.mkdir(directory)


def _copy_file(src, dst):
    with open(src, "rb") as src_file, open(dst, "wb") as dst_file:
        while True:
            chunk = src_file.read(4096)
            if not chunk:
                break
            dst_file.write(chunk)


def rollback(log_file, backup_directory="/backup"):
    try:
        # Check if the backup directory exists
        if not uos.path.exists(backup_directory):
            log_message("Backup directory not found", log_file)
            return False

        # Remove all existing files and directories
        for root, dirs, files in uos.walk("/"):
            for file in files:
                uos.remove(uos.path.join(root, file))
            for dir in dirs:
                uos.rmdir(uos.path.join(root, dir))

        # Restore files from the backup directory
        for root, dirs, files in uos.walk(backup_directory):
            for file in files:
                # Get the absolute path of the file in the backup directory
                backup_file = uos.path.join(root, file)

                # Get the corresponding path within the root directory
                restore_file = uos.path.join(
                    "/", uos.path.relpath(backup_file, backup_directory)
                )

                # Create the necessary directories in the root directory if they don't exist
                _makedirs(uos.path.dirname(restore_file))

                # Copy the file from the backup directory to the root directory
                _copy_file(backup_file, restore_file)

        # If everything goes well, return True
        log_message("Rollback successful", log_file)
        return True
    except Exception as e:
        log_message(f"Failed to rollback: {e}", log_file)
        return False
