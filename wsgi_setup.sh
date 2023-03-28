cp digidex.service /etc/systemd/system
chgrp www-data /root
systemctl start digidex
systemctl enable digidex
systemctl stop digidex
systemctl start digidex
systemctl disable digidex
systemctl enable digidex
systemctl daemon-reload