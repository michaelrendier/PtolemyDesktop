#!/usr/bin/bash

sudo sed -i 's/post_max_size = 2M/post_max_size = 200M/' /etc/php/7.2/apache2/php.ini &
sudo sed -i 's/upload_max_filesize = 2M/upload_max_filesize = 200M/' /etc/php/7.2/apache2/php.ini &
sudo sed -i 's/max_execution_time = 30/max_execution_time = 120/' /etc/php/7.2/apache2/php.ini &
sudo sed -i 's/max_input_time = 60/max_input_time = 120/' /etc/php/7.2/apache2/php.ini &
sudo sed -i 's/memory_limit = 128M/memory_limit = 512M/' /etc/php/7.2/apache2/php.ini