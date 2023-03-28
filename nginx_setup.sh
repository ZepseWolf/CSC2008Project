cp digidex_conf /etc/nginx/sites-available
ln -s /etc/nginx/sites-available/digidex_conf /etc/nginx/sites-enabled
unlink /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
ufw allow 'Nginx Full'