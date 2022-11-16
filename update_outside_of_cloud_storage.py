from datetime import datetime
import os
from pathlib import Path
from shutil import copy2
from typing import Any, NoReturn, Union


cloud_storage_files = []
list_for_delete = []
list_for_update = []


def check_file_operation(file_function):
    """Simple checker for exceptions in file operations."""
    def wrapper(*args, **kwargs) -> Any:
        try:
            result = file_function(*args, **kwargs)
        except Exception as error:
            input(f'\nThere something wrong with \"{file_function.__name__}\":\n{repr(error)}')
            return False
        return result
    return wrapper


@check_file_operation
def load_from_file(file_path: Path) -> list: 
    """Load data from file in path(file_path) to list, and return this list."""
    with open(str(file_path), 'r', encoding='utf-8-sig') as fh:  # check open str or path
        content = fh.readlines()
    content = [line.rstrip('\n') for line in content]
    return content


@check_file_operation
def save_to_file(file_path: Path, content: list) -> None: 
    """Save data to file in path(file_path) from list."""
    input(f'Write in file\n{file_path}\n')
    with open(str(file_path), 'w', encoding='utf-8-sig') as fh:  # encoding='utf_8'
        fh.writelines(content)


@check_file_operation
def delete_file(file_path: Path) -> None:
    """Simple delete file in path(file_path)."""
    file_path.unlink()


@check_file_operation
def copy_file(file: Path, path_disk: Path, name_upd_folder: str) -> None:
    """Copy file from path (file) to backup folder."""
    p0 = path_disk.joinpath(name_upd_folder)
    p1 = str(file.parent)[1:].replace(str(path_disk)[1:],'',1)
    p2 = p0.joinpath(p1[1:])
    target_path = p2.joinpath(file.name)
    # Create folders on path to file before copy
    target_path.parent.mkdir(exist_ok=True, parents=True)
    copy2(file, target_path)


@check_file_operation
def restore_file(file: Path, backup_folder_name: str) -> None:
    """Restore file from backup to tracking folder.
    """
    print(f'restore:\n{file}')
    print(f'backup_folder_name:\n{backup_folder_name}\n')
    p1 = str(file.parent).replace(f'{backup_folder_name}','',1)
    print(f'p1:\n{p1}')
    print(f'file.name:\n{file.name}\n')
    target_path = Path(p1).joinpath(file.name)
    print(f'target_path:\n{target_path}\n')
    target_path.parent.mkdir(exist_ok=True, parents=True)
    copy2(file, target_path)


@check_file_operation
def move_file(source_path: Path, target_path: Path) -> None:
    """Simple replace file(source_path) to folder(target_path)."""
    source_path.replace(target_path.joinpath(source_path.name)) # try...


@check_file_operation
def check_log_file(folder: Path) -> Union[Path, bool]:
    """Checking existence log file for backup (which contains the list of tracking files)."""
    for item in folder.iterdir():
        if item.is_file() and item.name[0].isdigit() and item.suffix == '.txt':
            return item
    return False


@check_file_operation
def check_active_backup(folder: Path) -> Union[Path, bool]:
    """Checking existence backup folder and check its actives."""
    for item in folder.iterdir():
        if item.is_dir() and item.name[0].isdigit():
            inner_log = check_log_file(item)
            if inner_log:
                return inner_log

    return False


@check_file_operation
def scanning(folder: Path) -> None:
    """
    Recursively scans the contents of folders and sub-folders,
    and filling the file lists.

        Parameters:
            folder(Path): A simple path of folder.

        Returns:
            None
    """
    for item in folder.iterdir():
        # If the current element is a folder scan this folder
        if item.is_dir():
            scanning(item)
            continue
    # Save a path of file if the element is not a folder
        cloud_storage_files.append(item)


def prepare_for_backup(targets_list: list) -> None:
    """Run scanning for each folder in targets list(tracking folders)."""
    for backup_folder in targets_list:
        if not Path(backup_folder).is_dir():
            print(f'\"{Path(backup_folder).name}\" - is not a folder, pass it.')
        else:
            scanning(Path(backup_folder))


@check_file_operation
def create_log_file(DIR_PATH) -> None:
    """Prepare list of paths(str), sizes, and fixing modified time of files,
    and save its list into file."""
    to_write = [f'{str(el)}\t{el.stat().st_size}\t{int(el.stat().st_mtime)}\n' for el in cloud_storage_files]
    name_log = str(datetime.now()).replace(':','_')
    name_log = name_log[:name_log.rfind('.')]
    save_to_file(DIR_PATH.joinpath(f'{name_log}.txt'), to_write)


@check_file_operation
def create_backup_from_log(path_disk: Path, name_upd_folder: str, log_new_backup: Path) -> None:
    """Create backup from the changed files."""
    backup_list = load_from_file(log_new_backup)
    backup_ = {}
    for item in backup_list:
        item = item.split('\t')
        backup_[str(item[0])] = [int(item[1]), int(item[2])]
    # backup changed files
    for file in backup_: 
        size = backup_[file][0]
        time = backup_[file][1]
        if not Path(file).exists():
            list_for_delete.append(file)
        elif int(Path(file).stat().st_size) != size or int(Path(file).stat().st_mtime) - time > 1:
            list_for_update.append(file)
            copy_file(Path(file), path_disk, name_upd_folder)
    # backup new created files
    for file in cloud_storage_files:
        if not backup_.get(str(file), None):
            list_for_update.append(file)
            copy_file(Path(file), path_disk, name_upd_folder)


@check_file_operation
def create_backup_lists(log_new_backup: Path, path_disk: Path, name_upd_folder: str) -> None:
    """Move backup log-file to backup folder, and save files, which incuding list of backaped files and files for removing."""
    folder_to_save = path_disk.joinpath(name_upd_folder)
    move_file(log_new_backup, folder_to_save)
    save_to_file(folder_to_save.joinpath('-'+str(log_new_backup.name)), [f'{item}\n' for item in list_for_delete])
    save_to_file(folder_to_save.joinpath('+'+str(log_new_backup.name)), [f'{item}\n' for item in list_for_update])
    

@check_file_operation
def create_new_backup(path_disk: Path, targets_list: list, log_new_backup: Path) -> None:
    """Create folder for new backup and fill it with files."""
    name_upd_folder = str(datetime.now().date())
    path_disk.joinpath(name_upd_folder).mkdir(exist_ok=True, parents=True)
    prepare_for_backup(targets_list)  # all real files now in cloud_storege_files
    create_backup_from_log(path_disk, name_upd_folder, log_new_backup)
    create_backup_lists(log_new_backup, path_disk, name_upd_folder)


@check_file_operation
def restore_from_backup(log_active_backup: Path, path_disk: Path, arch_folder: str) -> None:
    """Restoring new files from backup, after save(removing to Archive-folder) old files."""
    parent_folder = log_active_backup.parent
    name = log_active_backup.name
    list_for_delete1 = load_from_file(parent_folder.joinpath('-'+str(name)))
    list_for_update1 = load_from_file(parent_folder.joinpath('+'+str(name)))

    if list_for_delete1:
        for file in list_for_delete1:
            copy_file(Path(file), path_disk, arch_folder)  # copy_file(file: Path, path_disk: Path, name_upd_folder: str):
            delete_file(Path(file))
    # delete log_active_backup - backup folder will be unactive.
    delete_file(log_active_backup)

    if list_for_update1:
        for file in list_for_update1:
            if Path(file).exists():
                copy_file(Path(file), path_disk, arch_folder)
                delete_file(Path(file))
   
    prepare_for_backup([parent_folder]) # new files to list: cloud_storage_files

    for file in cloud_storage_files:

        restore_file(Path(file), str(parent_folder).replace(str(parent_folder.parent),''))
    

def main() -> NoReturn:
    """The main function of launching whole process.
    """
    # Path of current work directory
    DISK_PATH = Path(os.path.abspath(os.getcwd())) # Path(__file__).parent # Path(sys.path[0])
    # Path of "config.txt"
    config = DISK_PATH.joinpath('config.txt')
    # If not exist "config.txt" in the DISK_PATH - then exit()
    if not config.exists():
        input(f'No targets (missing \"config.txt\"):\n{config}\n Press \"Enter\" to exit. ')
        exit()
    
    input(f'Catch\n{config}\n Press \"Enter\" to next step... ')
    # From "config.txt" load folders for tracking into targets_list
    targets_list = load_from_file(config)
    input(f'Loaded:\n{targets_list}\n')
    # Get path of backup log file (list of all files from folders for tracking (targets_list)) in backup folder if it exist
    log_active_backup = check_active_backup(DISK_PATH)
    # Get path of backup log file in current work directory
    log_new_backup = check_log_file(DISK_PATH)
    # Create name for archive folder (for files which will be deleted or repleced)
    arch_folder = f'Ar{datetime.now().date()}'
    # If Exist active backup folder (active - which contains backup log file)
    if log_active_backup:
        input('Phase 1 restore from backup')
        restore_from_backup(log_active_backup, DISK_PATH, arch_folder)
    # if active backup folder does not exist, but exist backup log file into current work directory
    elif log_new_backup:
        input('Phase 2 create new backup')
        create_new_backup(DISK_PATH, targets_list, log_new_backup)
    else:
        input('Phase 3 create list of current files for tracking')
        prepare_for_backup(targets_list)
        create_log_file(DISK_PATH)
    
    input('\nDone. All right? Press Enter to exit.')

if __name__ == '__main__':
    main()
