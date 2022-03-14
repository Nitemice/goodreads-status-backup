# goodreads-status-backup

This is a Python script for backing up your statuses from Goodreads.

It is spun out of
[Nitemice/goodreads-backup](https://github.com/Nitemice/goodreads-backup).
That script no longer works (for new users, at least), due to changes to the
Goodreads API.

## Installation

This script requires Python 3. Create a virtualenv and install dependencies:

```shell
$ virtualenv env
$ source env/Scripts/activate
$ pip install -r requirements.txt
```

You need to set up two things before you can use the script:

1.  Make your Goodreads statuses public. This script only scrapes public pages,
    so private statuses can't be backed up.
2.  Get your Goodreads user ID. This is the 8-digit number in the URL of
    your profile page. For example, if your user page is
    `https://www.goodreads.com/user/show/12345678-john-smith`, then your
    user ID is `12345678`.

## Usage

Run the script, passing your user ID as a command-line flag:

```shell
$ python backup_goodreads.py --user-id=12345678
```

Alternatively, a config file can be used to specify these details.
See below for an example:
```json
{
    "user_id": "12345678"
}
```

To see other options, run with the ``--help`` flag:

```shell
   $ python backup_goodreads.py --help
```

## License

This script is licensed under the MIT license.
