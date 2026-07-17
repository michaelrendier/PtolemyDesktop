from netmiko import ConnectHandler
import getpass,sys,time

cisco_3725 = {'device_type': 'cisco_ios',
               'ip': '192.168.43.10',
               'username': 'username',
               'password': 'password'
}

iosv_l2_s1 = {'device_type': 'cisco_ios',
               'ip': '192.168.43.2',
               'username': 'username',
               'password': 'password'
}

iosv_l2_s2 = {'device_type': 'cisco_ios',
               'ip': '192.168.43.3',
               'username': 'username',
               'password': 'password'
}


iosv_l2_s3 = {'device_type': 'cisco_ios',
               'ip': '192.168.43.4',
               'username': 'username',
               'password': 'password'
}



all_devices = [iosv_l2_s1, iosv_l2_s2, iosv_l2_s3]



def run_command_on_pri_mode(deviceName):
	
	config_commands = ['no ip domain-lookup',
					   'service password-encryption',
					   'service timestamps log datetime msec',
					   'service timestamps debug datetime msec',
					   'line cons 0',
					   'logging synchronous',
					   'exec-timeout 5 0',
					   'password cisco'
					   ]
					   
    answer_1 = raw_input('Would you run a command on the privilege mode on the device {0}?\nEnter [Y/N]: '.format(deviceName))

    # ~ if (answer_1 == 'Y') or (answer_1 == 'y'):
    if answer_1.upper() == "Y":

		for i in config_commands:
			print(config_commands.index(i), i)
			
		privilege_mode_command = raw_input('Enter the command : ')
		# ~ if privilege_mode_command in config_commands:
			# ~ output = net_connect.send_command(privilege_mode_command)
		# ~ print(output)
		try:
			output = net_connect.send_command(privilege_mode_command)
		except:
			run_command_on_pri_mode(deviceName)
      
		answer_2 = raw_input("Would you run another command on the device {0}?\nEnter [Y/N]: ".format(deviceName))
      
		if answer_2.upper() == "Y":
			run_command_on_pri_mode(deviceName)
		else:
			return

    # ~ while answer_1 == 'Y' or answer_1 == 'y':

        # ~ answer_2 = raw_input('Would you run another command on the device ' + deviceName + '?' + '\n' + 'Enter [Y/N]: ')

        # ~ if (answer_2 == 'Y') or (answer_2 == 'y'):
          # ~ privilege_mode_command = raw_input('Enter the new command : ')
          # ~ output = net_connect.send_command(privilege_mode_command)
          # ~ print(output)
        # ~ else:
           # ~ break


def basic_config(deviceName):

    answer_3 = raw_input('Would you run the basic configuration on the device ' + deviceName + '?' + '\n' + 'Enter [Y/N]: ')

    if (answer_3 == 'Y') or (answer_3 == 'y'):

    # while 1:
    #    change_config = raw_input('Enter the command : ')
    #    if change_config != 'exit':
    #      output = net_connect.send_config_set(change_config)
    #      print(output)
    #    else:
    #      break

     print("The basic configuration on device " + deviceName + ':')
     config_commands = ['no ip domain-lookup',
                       'service password-encryption',
                       'service timestamps log datetime msec',
                       'service timestamps debug datetime msec',
                       'line cons 0',
                       'logging synchronous',
                       'exec-timeout 5 0',
                       'password cisco'
                       ]

     output = net_connect.send_config_set(config_commands)
     print(output)


def vlans_config(deviceName):

    answer_4 = raw_input('Would you run the VLANs configuration on device ' +  deviceName + '?' + '\n' + 'Enter [Y/N]: ')

    if (answer_4 == 'Y') or (answer_4 == 'y'):

      vlan_nbr = raw_input('How many VLAN do you want to create ? ' + '\n' + 'Enter the value: ')
      vlan_nbr = int(vlan_nbr)
      print("Configuration the VLANs on device " + deviceName + ':')

      for n in range (2,(vlan_nbr + 2)):
          print("Creating Vlan " + str(n))
          name_vlan = raw_input('Enter the VLAN name: ')
          config_vlans = ['vlan ' + str(n),
                         'name ' + name_vlan
                         ]
          output = net_connect.send_config_set(config_vlans)
          print(output)

def file_config(deviceName):

    answer_4 = raw_input('Would you run configurations saved on a file on device ' +  deviceName + '?' + '\n' + 'Enter [Y/N]: ')

    if (answer_4 == 'Y') or (answer_4 == 'y'):

      file_name = raw_input("Enter the file name: ")
      with open(file_name) as file:
           lines = file.read().splitlines()
           print(lines)

      output = net_connect.send_config_set(lines)
      print(output)

def save_running_config(deviceName):

    answer_6 = raw_input('Would you save the current configuartion on device ' +  deviceName + ' to NVRAM?' + '\n' + 'Enter [Y/N]: ')

    if (answer_6 == 'Y') or (answer_6 == 'y'):
       save_config = net_connect.send_command('wr')
       print('save_config')
       print('The configuration was written to NVRAM successfully')

def get_config(deviceName):

    answer_6 = raw_input('Would you save the output of the current configuartion on device ' +  deviceName + ' to a file on your host?' + '\n' + 'Enter [Y/N]: ')

    if (answer_6 == 'Y') or (answer_6 == 'y'):
       net_connect.send_command('terminal lenth 0')
       output = net_connect.send_command('sho run')
       file_name_saved = raw_input("Enter the file name: ")
       #saveoutput = open('Cisco_Device ' + deviceName, "w")
       saveoutput = open(file_name_saved, "w")
       saveoutput.write(output)
       saveoutput.close


### Establish an SSH connection to the device:

try_nbr = 3

while try_nbr != 0:

    connection = raw_input('Which device you want to connect ?' + '\n' + 'Enter the answer: ')

### Connection to all devices:

    if (connection == 'All') or (connection == 'all'):
     try_nbr = try_nbr - 2
     for device in all_devices:
        print("Authentication on the device " + device['ip'])
        device['username'] = raw_input('Username: ')
        device['password'] = getpass.getpass()
        net_connect = ConnectHandler(**device)
        print('Successfull connection ' + device['ip'])
        run_command_on_pri_mode(device['ip'])
        basic_config(device['ip'])
        vlans_config(device['ip'])
        file_config(device['ip'])
        save_running_config(device['ip'])
        get_config(device['ip'])
        print('Close the connection ' + device['ip'])
        print

### Connection to switch iosv_l2_s1:

    elif (connection == 'iosv_l2_s1'):
      try_nbr = try_nbr - 2
      print("Authentication on the device " + iosv_l2_s1['ip'])
      iosv_l2_s1['username'] = raw_input('Username: ')
      iosv_l2_s1['password'] = getpass.getpass()
      net_connect = ConnectHandler(**iosv_l2_s1)
      print('Successfull connection ' + iosv_l2_s1['ip'])
      run_command_on_pri_mode(iosv_l2_s1['ip'])
      basic_config(iosv_l2_s1['ip'])
      vlans_config(iosv_l2_s1['ip'])
      file_config(iosv_l2_s1['ip'])
      save_running_config(iosv_l2_s1['ip'])
      get_config(iosv_l2_s1['ip'])
      print('Close the connection ' + iosv_l2_s1['ip'])
      print

### Connection to switch iosv_l2_s2:

    elif (connection == 'iosv_l2_s2'):
      try_nbr = try_nbr - 2
      print("Authentication on the device " + iosv_l2_s2['ip'])
      iosv_l2_s2['username'] = raw_input('Username: ')
      iosv_l2_s2['password'] = getpass.getpass()
      net_connect = ConnectHandler(**iosv_l2_s2)
      print('Successfull connection ' + iosv_l2_s2['ip'])
      run_command_on_pri_mode(iosv_l2_s2['ip'])
      basic_config(iosv_l2_s2['ip'])
      vlans_config(iosv_l2_s2['ip'])
      file_config(iosv_l2_s2['ip'])
      save_running_config(iosv_l2_s2['ip'])
      get_config(iosv_l2_s2['ip'])
      print('Close the connection ' + iosv_l2_s2['ip'])
      print

### Connection to switch iosv_l2_s3:

    elif (connection == 'iosv_l2_s3'):
      try_nbr = try_nbr - 2
      print("Authentication on the device " + iosv_l2_s3['ip'])
      iosv_l2_s3['username'] = raw_input('Username: ')
      iosv_l2_s3['password'] = getpass.getpass()
      net_connect = ConnectHandler(**iosv_l2_s3)
      print('Successfull connection ' + iosv_l2_s3['ip'])
      run_command_on_pri_mode(iosv_l2_s3['ip'])
      basic_config(iosv_l2_s3['ip'])
      vlans_config(iosv_l2_s3['ip'])
      file_config(iosv_l2_s3['ip'])
      save_running_config(iosv_l2_s3['ip'])
      get_config(iosv_l2_s3['ip'])
      print('Close the connection ' + iosv_l2_s3['ip'])
      print

### Exit the connection if name does not match:

    else:
      try_nbr = try_nbr - 1
      print('Device not found!!')
