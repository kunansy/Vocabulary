from backup_auth import Auth
from constants import DATA


def main():
    content_backup = Auth()

    content_backup.upload_file('content', DATA)


if __name__ == "__main__":
    main()