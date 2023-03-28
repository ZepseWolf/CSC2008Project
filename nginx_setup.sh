cp edoc_conf /etc/nginx/sites-available
ln -s /etc/nginx/sites-available/edoc_conf /etc/nginx/sites-enabled
unlink /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx
ufw allow 'Nginx Full'