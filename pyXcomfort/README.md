# How to use the integration

To install add-ons, navigate to the [Settings > Add-ons panel](https://my.home-assistant.io/redirect/supervisor/) in your Home Assistant frontend, and click on the "Add-on store" tab. All add-ons, including their documentation, are available right from the store. Some advanced add-ons will only be visible after you opt-in to "Advanced Mode" which can be changed on your user profile page. Click on an add-on you are interested in, to read the documentation or to install the add-on.

<img width="194" height="73" alt="image" src="https://github.com/user-attachments/assets/fd34adc9-3641-4d16-87e9-a0857cc30e0a" />



## Add Xcomfort configuration.yaml

You should be able to just select the correct device from a dropdown, like this:

<img width="1047" height="610" alt="image" src="https://github.com/user-attachments/assets/12f898d3-a318-484a-a72f-ec54cc01fefa" />

Then you can add your devices one at the time with this:

<img width="416" height="334" alt="image" src="https://github.com/user-attachments/assets/5c4b7820-1247-4355-944a-fd77b6f0df18" />

Or switch to yaml-mode and add something like this:

```yaml
xcomfort:
  device: /dev/ttyUSB0 # default
  timeout: 10 # For how many seconds the binary sensor to be "on" after a button push. Default 240
  switches:
    - serial: 5109324
      name: Wallswitch Livingroom
  devices:
    - serial: 2118499
      name: Pendel
    - serial: 5077172
      name: Plafond
```
Where do I get the serial from? You need to look in the [Eaton MRF software](http://www.eaton.eu/Europe/Electrical/ProductsServices/Residential/xComfort-RFSmartHomeSolutions/PCT_1118492#tabs-11)

![Eaton MRF File menu](https://github.com/user-attachments/assets/20006a49-deb2-485a-94ca-ffa4b228c844)

Open File > Details about components

![Eaton MRF Detail screen](https://github.com/user-attachments/assets/c365fe85-4e34-48d4-a516-a91c9d104257)

Look at the Serienummer column (serial number). I have removed mine, but hopefully you will find your there.

After saving you will be prompted to restart the add-on. And since the add-on and home assistant is now decoupled you do not need to restart HA for every change you make! 
