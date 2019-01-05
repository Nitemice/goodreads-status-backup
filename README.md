# backup-goodreads

This is a Python script for backing up your reviews, shelves and statuses from 
Goodreads.
It is based on both 
(bjaanes/goodreads-backup)[https://github.com/bjaanes/goodreads-backup] and 
(alexwlchan/backup-goodreads)[https://github.com/alexwlchan/backup-goodreads].

## Installation

This script requires Python 3. Create a virtualenv and install dependencies:

```shell
$ virtualenv env
$ source env/bin/activate
$ pip install -r requirements.txt
```

You need to set up three things before you can use the script:

1.  Make your Goodreads reviews public. This script only uses the basic
    API, not OAuth, and so private reviews can't be backed up.
2.  Get your Goodreads user ID. This is the 8-digit number in the URL of
    your profile page. For example, if your user page is
    `https://www.goodreads.com/user/show/12345678-john-smith`, then your
    user ID is `12345678`.
3.  Get a [developer API key](https://www.goodreads.com/api/keys) from
    the Goodreads website.

## Usage

Run the script, passing your user ID and API key as command-line flags:

```shell
$ python backup_goodreads.py --user-id=12345678 --api-key=abcdefg123
```
Alternatively, these details can be set using `keyring`.
See (its documentation)[https://pypi.org/project/keyring/#command-line-utility]
for how this is done.  

To see other options, run with the ``--help`` flag:

```shell
   $ python backup_goodreads.py --help
```

## License

This script is licensed under the MIT license.