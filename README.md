giFTP
=====

Simple utilty to simplify working with GIT and FTP. Upload only files that has been changed to the server.

No more guessing work which file are changed, deleted and added.

This program take advantage of **GIT diff** to determines changes in file. **giFTP** is built on top of **GitPython** library to interface with GIT.

Installation
------------

    1. Get giFTP from : https://github.com/ekaputra07/giFTP/archive/master.zip
    2. Extract it and run: python setup.py install
    3. Once installed, this program are ready to be used.
    
Usage
-----

Once installed, giFTP are available in your system by running **<code>gtp</code>** in your console.

**1. Create config file :**

giFTP use a JSON file called <code>gtp.json</code> to store information about your target Git repository and your FTP credentials.

To create config file is easy, just run:

    $ gtp --init
    > Config file has been generated...
    > Now edit "gtp.json" and fill with your FTP and GIT information.
    
It will create a file <code>gtp.json</code> in the same directory you call this program, thats why its better to create this config inside your web project.

Once config created, you can open it and edit to match your Repo and FTP information, example:

    {
        "repo": {
            "path": "/absolute/path/to-your/git-repo", 
            "latest_commit": "56f17fad9471327aa2f60c6aec4cc8f4d9bf9870, 
            "branch": "master"
        }, 
        "host": {
            "url": "example.com", 
            "username": "", 
            "password": "", 
            "path": "wp-content/themes/mythemes"
        }
    }

The config itself is self explanatory, 

    Repo:
     - path : is path to your git repository/working area.
     - latest_commit : In which commit id this program will try to track for changes. To get this value use "git log" command on your git repo to get the latest commit id.
     - branch : Branch to watch for changes.
     
    Host:
     - path : Remote path on the server that file will be transferred.

After config has been set, lets check if your FTP informations are correct.

**2. Test connection :**

After config has been set, its time to test it.

    $ gtp --test
    > [INFO] Connecting...
    > [INFO] Connection success.
    
If it success, now you can make any changes to the repo and make a commit.

**3. Apply changes to remote server :**

Before doing any actual update, we can check what actions that will be run by giFTP, by doing a simulation.

Simulation will show us actual update process on the console, but not doing any actual changes to the server. Start it with:

    $ gtp --simulate

When you are ready to deploy changes, just run this command in the same directory your config file are located:

    $ gtp --update
    > [INFO] Checking repository...
    > [INFO] Found 2 new commit...
    
    > [INFO] Processing commit: Some image cleanup
    > |__[INFO] Deleting [26baa5db499f529fecb63d84604fc642.jpeg]...
    > |__[INFO] Deleting [65038_708187192529450_819581801_n.jpg]...
    > |__[INFO] Deleting [New/26baa5db499f529fecb63d84604fc642.jpeg]...
    > |__[INFO] Deleting [New/65038_708187192529450_819581801_n.jpg]...
    
    > [INFO] Processing commit: Add hello.txt
    > |__[INFO] Adding [hello.txt]...
    
And thats it, if all config information correct, giFTP will update all changes via FTP connection.

Todo
----
giFTP is just a single day old when I created this simple docs, there are lots of things that can be improved and and added.

Please don't blame for any damage that caused by this program when it goes wild or you FTP secret being seen by others.

Please test first before use it for production site.

More thing to do:

 * Automate to detect the current GIT head ID, to avoid set it manually when initialize giFTP for the first time.
 * Add a way to store FTP password more securely.