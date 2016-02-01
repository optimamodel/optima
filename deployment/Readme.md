The deployment of the platform is automated thanks to the use of Prudentia.

To install Prudentia please refer to this https://github.com/StarterSquad/prudentia#install.

Once Prudentia is setup run it using the vagrant provider.

`$ prudentia vagrant`

Prudentia is based on a command line interface with which you can interact to create boxes and provision them.
 
Let's start of registering a new box that will prompt you with several questions, here is an example session:

```
(Prudentia > Vagrant) register
Specify the playbook path: /<Path_to_Optima_dir>/deployment/boxes/staging.yml
Specify the box name [default: optima-staging]: 
Specify the internal IP: 10.0.0.11
Specify the amount of RAM in GB [default: 1]: 3 (1 is not enough to build matplotlib)
Do you want to share a folder? [default: N]: y
Specify the directory on the HOST machine: /<Path_to_Optima_dir>
Specify the directory on the GUEST machine: /opt/optima
Do you want to share a folder? [default: N]: 
Bringing machine 'optima-staging' up with 'virtualbox' provider...
```

in the above example replace <Path_to_Optima_dir> with the full path of your project directory.

Once the box has been created you can then provision it:

`(Prudentia > Vagrant) provision optima-staging`

this may take some time depending on your computer performance.

Once the provisioning is done you can access http://10.0.0.11.


AWS Installation
------------------

Steps for new release:

 - Open AWS console in N.Virginia region
 - Start the instance i-310d97c0
 - Start the optima-prod-deploy job
 - Wait till done
 - (Recommended) log on to the instance (by IP) and verify that it has restarted with the new version
 - Create an AMI from this instance (call it as the release number)
 - Create a new LaunchConfiguration using the new AMI
 - Configure the existing AutoScaling group to use the new LaunchConfiguration
 - Remove the previous LaunchConfiguration
 - Remove the previous instances (They don't seem to shut down by themselves) and verify that the AutoScaling group restarted the new instance 
 - Go to optima.startersquad.com and verify that the application works
 - Stop the instance i-310d97c0
