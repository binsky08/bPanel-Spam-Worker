# bPanel Spam Worker

bPanel SpamWorker is a custom sa-learn background worker

## Requirements

`apt-get install python3 spamassassin`

## Installation

```
cd /opt/bpanel
git clone https://git.binsky.org/binsky/bPanelSpamWorker.git spamWorker
cp ./spamWorker/bpanel-spam-worker.service /lib/systemd/system/
chown www-data /opt/bpanel/spamWorker
systemctl enable bpanel-spam-worker
systemctl start bpanel-spam-worker
```

Edit these three lines in `/var/lib/roundcube/plugins/markasjunk2/config.inc.php`
```
$config['markasjunk2_learning_driver'] = 'cmd_learn';
$config['markasjunk2_spam_cmd'] = '/usr/bin/python3 /opt/bpanel/spamWorker/bPanelSpamWorkerClient.py --spam -u "%u" -f "%f"';
$config['markasjunk2_ham_cmd'] = '/usr/bin/python3 /opt/bpanel/spamWorker/bPanelSpamWorkerClient.py --ham -u "%u" -f "%f"';
```
