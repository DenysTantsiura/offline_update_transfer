from datetime import datetime
import sys
from pathlib import Path
from shutil import copy2
from typing import NoReturn

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
        # If the current element is a folder,
        # add it to the FOLDERS list and check the next element
        # (after scanning this new folder).
        if item.is_dir():
            scanning(item)

            continue

    # Working with a file if the element is not a folder
        cloud_storage_files.append(item)

def check_log_file(folder):
    for item in folder.iterdir():
        if item.is_file():
            if item.name[0].isdigit() and item.suffix == '.txt':
                return item

    return False

def check_upd_folder(folder):
    for item in folder.iterdir():
        if item.is_dir() and item.name[0].isdigit():
            inner_log = check_log_file(item)
            if inner_log:
                return inner_log

    return False

def scan_report(config):
    with open(config, 'r', encoding='utf-8-sig') as fh:  # encoding='utf_8'
        cloud_paths = fh.readlines()
    cloud_paths = [line.rstrip('\n') for line in cloud_paths]    
    # print(cloud_paths)
    
    for cloud_path in cloud_paths:
        if not Path(cloud_path).is_dir():
            print(f'\"{Path(cloud_path).name}\" - is not a folder, pass it.')
        else:
            scanning(Path(cloud_path))
            path_disk = Path(cloud_path).parent

    return path_disk


def create_update(path_disk, log_file):
    name_upd_folder = str(datetime.now().date())
    Path(name_upd_folder).mkdir(exist_ok=True, parents=True)
    # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
    # scan_report(config)

    with open(str(log_file), 'r', encoding='utf-8-sig') as fh:
        while True:
            current_file = fh.readline().split('\t')
            if len(current_file) < 3:
                break
            file = Path(current_file[0])
            if not file.exists():
                print(f'!Old file must be deleted?: \n{file}')
                # if input('y or n? ') == 'y':
                #     file.unlink()
                continue

            size = int(current_file[1])
            time = int(current_file[2].rstrip('\n'))
            if int(file.stat().st_size) != size or int(file.stat().st_mtime) - time > 1:
                # копіюємо змінені файли
                # print(f's0:\n{path_disk}')
                # print(f's1:\n{name_upd_folder}')
                # print(f'''s2:\n{str(file.parent).replace(str(path_disk),'',1)}''')
                # print(f's3:\n{file.name}')
                update_file = ((path_disk.joinpath(name_upd_folder)).joinpath(str(file.parent).replace(str(path_disk),'',1)[1:])).joinpath(file.name)
                # print(f'update_file:\n{update_file}')
                update_file.parent.mkdir(exist_ok=True, parents=True)
                # print(f'update_file:\n{update_file}')
                # print(f'\nFrom:\n{file}\nTo:\n{update_file}\n')
                copy2(file, update_file)

            cloud_storage_files.remove(file)
            # print(f'\n-from list removed file:\n{file}\n')

    Path(log_file).replace(path_disk.joinpath(name_upd_folder).joinpath(Path(log_file).name)) 

    for new_file in cloud_storage_files:
        # копіюємо нові файли 
        update_file = ((path_disk.joinpath(name_upd_folder)).joinpath(str(new_file.parent).replace(str(path_disk),'',1)[1:])).joinpath(new_file.name)
        update_file.parent.mkdir(exist_ok=True, parents=True)
        # print(f'\nNew from:\n{new_file}\nTo:\n{update_file}\n')
        copy2(file, update_file)

           
    # по завершенні переносимолог-файл до папки апдейта
    # print(name_upd_folder)

def create_fix_file(DIR_PATH):
    to_write = [f'{str(el)}\t{el.stat().st_size}\t{int(el.stat().st_mtime)}\n' for el in cloud_storage_files]

    name_log = str(datetime.now()).replace(':','_')
    name_log = name_log[:name_log.rfind('.')]
    with open(DIR_PATH.joinpath(f'{name_log}.txt'), 'w', encoding='utf-8-sig') as fh:  # encoding='utf_8'
        fh.writelines(to_write)

def unpack_updates(upd_file_log):
    # if not file.exists():
    #     print(f'!Old file must be deleted?: \n{file}')
    #     if input('y or n? ') == 'y':
    #         file.unlink()
    #     continue
    print(f'{upd_file_log.parent}')

    # upd_file_log.unlink()
    


def main() -> NoReturn:
    """The main function of launching ...
    """
    DIR_PATH = Path(__file__).parent # Path(sys.path[0])
    config = DIR_PATH.joinpath('config.txt')
    if not config.exists():
        input('No tasks (missing \"config.txt\"). Press \"Enter\" to exit. ')
        exit()

    upd_folder_log_file = check_upd_folder(DIR_PATH)
    if upd_folder_log_file:
        unpack_updates(upd_folder_log_file)  # !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        # dell inner log in up function
  #      main()  # !!!!!!!!!!!!
        # exit()
    else:
        log_file = check_log_file(DIR_PATH)
        if log_file:
            # print(log_file)
            create_update(scan_report(config), log_file)
            # and move into - log_file
        else:
            scan_report(config)
            create_fix_file(DIR_PATH)
        
       
        # create_update()




    # print(cloud_storage_files)



    # with open(DIR_PATH.joinpath(f'{name_log}.txt'), 'r', encoding='utf-8-sig') as fh:  # encoding='utf_8'
    #     print(fh.readlines())

    # print(DIR_PATH := Path(sys.path[0]))
    # print(Path(__file__).parent)

    # if not exist config.txt - exit()
    # else: try read not ok - exit
    # else: 
    # if not exist *(data).csv:
        # scan way create list(file path, date, size)
        # and save it in (data).csv
# !!!!!!!!!!!! ? copy to file with create parrent dirr?
    #  else (if exist *(data).csv:)
        # scan way create list(file path, date, size)  
        # and compare it within into data.csv if in 



if __name__ == '__main__':
    main()
