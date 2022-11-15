from datetime import datetime
import sys  # ?
from pathlib import Path
from shutil import copy2
from typing import NoReturn


def check_file_operation(file_function):
    def wrapper(*args, **kwargs):
        try:
            result = file_function(*args, **kwargs)
        except Exception as error:
            print(f'\nThere something wrong with \"{file_function.__name__}\":\n{repr(error)}')
            return False
        return result
    return wrapper


@check_file_operation
def load_from_file(file_path: Path) -> list: # try...
    with open(str(file_path), 'r', encoding='utf-8-sig') as fh:  # check open str or path
        content = fh.readlines()
    content = [line.rstrip('\n') for line in content]
    return content


@check_file_operation
def save_to_file(file_path: Path, content: list): # try...
    with open(str(file_path), 'w', encoding='utf-8-sig') as fh:  # encoding='utf_8'
        fh.writelines(content)


@check_file_operation
def delete_file(file_path: Path):
    file_path.unlink()  # try...


@check_file_operation
def copy_file(file: Path, path_disk: Path, name_upd_folder: str):
    p0 = path_disk.joinpath(name_upd_folder)
    p1 = str(file.parent)[1:].replace(str(path_disk)[1:],'',1)
    p2 = p0.joinpath(p1[1:])
    target_path = p2.joinpath(file.name)
    target_path.parent.mkdir(exist_ok=True, parents=True)
    copy2(file, target_path)


@check_file_operation
def move_file(source_path: Path, target_path: Path):
    source_path.replace(target_path.joinpath(source_path.name)) # try...

def check_log_file(folder):
    for item in folder.iterdir():
        if item.is_file() and item.name[0].isdigit() and item.suffix == '.txt':
            return item
    return False

def check_active_backup(folder):
    for item in folder.iterdir():
        if item.is_dir() and item.name[0].isdigit():
            inner_log = check_log_file(item)
            if inner_log:
                return inner_log

    return False


cloud_storage_files = []


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


def prepare_for_backup(targets_list: list) -> Path:
    for backup_folder in targets_list:
        if not Path(backup_folder).is_dir():
            print(f'\"{Path(backup_folder).name}\" - is not a folder, pass it.')
        else:
            scanning(Path(backup_folder))
            # path_disk = Path(backup_folder).parent
    return  # path_disk

list_for_delete = []
list_for_update = []

@check_file_operation
def create_log_file(DIR_PATH):
    to_write = [f'{str(el)}\t{el.stat().st_size}\t{int(el.stat().st_mtime)}\n' for el in cloud_storage_files]
    name_log = str(datetime.now()).replace(':','_')
    name_log = name_log[:name_log.rfind('.')]
    save_to_file(DIR_PATH.joinpath(f'{name_log}.txt'), to_write)

def create_backup_from_log(path_disk: Path, name_upd_folder: str, log_new_backup: Path):

    backup_list = load_from_file(log_new_backup)
    backup_ = {}
    for item in backup_list:
        item = item.split('\t')
        backup_[str(item[0])] = [int(item[1]), int(item[2])]
    
    for file in backup_:  # cloud_storage_files
        size = backup_[file][0]
        time = backup_[file][1]
        if not Path(file).exists():
            list_for_delete.append(file)
        elif int(Path(file).stat().st_size) != size or int(Path(file).stat().st_mtime) - time > 1:
            list_for_update.append(file)
            copy_file(Path(file), path_disk, name_upd_folder)

    for file in cloud_storage_files:
        if not backup_.get(str(file), None):
            list_for_update.append(file)
            copy_file(Path(file), path_disk, name_upd_folder)

def create_backup_lists(log_new_backup: Path, path_disk: Path, name_upd_folder: str):
    folder_to_save = path_disk.joinpath(name_upd_folder)
    move_file(log_new_backup, folder_to_save)
    save_to_file(folder_to_save.joinpath('-'+str(log_new_backup.name)), [f'{item}\n' for item in list_for_delete])
    save_to_file(folder_to_save.joinpath('+'+str(log_new_backup.name)), [f'{item}\n' for item in list_for_update])
    

def create_new_backup(path_disk: Path, targets_list: list, log_new_backup: Path):
    name_upd_folder = str(datetime.now().date())
    path_disk.joinpath(name_upd_folder).mkdir(exist_ok=True, parents=True)
    prepare_for_backup(targets_list)  # all real files now in cloud_storege_files
    create_backup_from_log(path_disk, name_upd_folder, log_new_backup)
    create_backup_lists(log_new_backup, path_disk, name_upd_folder)

def restore_from_backup(log_active_backup: Path, path_disk: Path, arch_folder: str):
    parent_folder = log_active_backup.parent
    name = log_active_backup.name
    list_for_delete1 = load_from_file(parent_folder.joinpath('-'+str(name)))
    list_for_update1 = load_from_file(parent_folder.joinpath('+'+str(name)))

    if list_for_delete1:
        for file in list_for_delete1:
            copy_file(Path(file), path_disk, arch_folder)  # copy_file(file: Path, path_disk: Path, name_upd_folder: str):
            delete_file(Path(file))

    delete_file(log_active_backup)

    if list_for_update1:
        for file in list_for_update1:
            if Path(file).exists():
                copy_file(Path(file), path_disk, arch_folder)
                delete_file(Path(file))
            # copy_file(..,..,..)

    prepare_for_backup([parent_folder]) # new files to list: cloud_storage_files

    for file in cloud_storage_files:

        copy_file(Path(file), Path('D:\\projects\\offline_update_transfer'), '')
    

def main() -> NoReturn:
    """The main function of launching ...
    """
    DISK_PATH = Path(__file__).parent # Path(sys.path[0])
    config = DISK_PATH.joinpath('config.txt')

    if not config.exists():
        input('No targets (missing \"config.txt\"). Press \"Enter\" to exit. ')
        exit()

    targets_list = load_from_file(config)

    log_active_backup = check_active_backup(DISK_PATH)
    log_new_backup = check_log_file(DISK_PATH)
    arch_folder = f'Ar{datetime.now().date()}'

    if log_active_backup:
        restore_from_backup(log_active_backup, DISK_PATH, arch_folder)
    elif log_new_backup:
        create_new_backup(DISK_PATH, targets_list, log_new_backup)
    else:
        prepare_for_backup(targets_list)
        create_log_file(DISK_PATH)

    
    input('\nFinish, everythink is Ok. Press Enter to exit. ')

if __name__ == '__main__':
    main()
