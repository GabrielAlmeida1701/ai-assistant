def info(obj):
    _save_log_file(f'[INFO] {str(obj)}')

def warning(obj):
    _save_log_file(f'[WARN] {str(obj)}')

def error(obj):
    _save_log_file(f'[ERROR] {str(obj)}')

def _save_log_file(obj):
    try:
        file = open('./resources/log_file.log', 'a')
        file.write(obj)
        file.write('\n')
        file.close()
    except:
        pass
    print(obj)