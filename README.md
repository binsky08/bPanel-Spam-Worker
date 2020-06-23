# bPanel Spam Worker

bPanel SpamWorker is a custom sa-learn background worker

## Requirements

`apt-get install python3 spamassassin`

## Installation

```
cd /opt/bpanel
git clone https://git.binsky.org/binsky/bPanelSpamWorker.git spamWorker
cp ./spamWorker/bpanel-spam-worker.service /lib/systemd/system/
mkdir -p /var/run/bpanel
chown www-data /opt/bpanel/spamWorker /var/run/bpanel
systemctl enable bpanel-spam-worker
systemctl start bpanel-spam-worker
sed -e '/unlink($tmpfname);/ s=^/*=//=' -i /var/lib/roundcube/plugins/markasjunk2/drivers/cmd_learn.php
```

Edit these three lines in `/var/lib/roundcube/plugins/markasjunk2/config.inc.php`
```
$config['markasjunk2_learning_driver'] = 'cmd_learn';
$config['markasjunk2_spam_cmd'] = '/usr/bin/python3 /opt/bpanel/spamWorker/bPanelSpamWorkerClient.py --spam -u "%u" -f "%f"';
$config['markasjunk2_ham_cmd'] = '/usr/bin/python3 /opt/bpanel/spamWorker/bPanelSpamWorkerClient.py --ham -u "%u" -f "%f"';
```
