<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="utf-8">
    <title>Shutdown</title>
  </head>
  <body>
    <p>The board is shutting down, wait for the power LED (green) to turn off then disconnect the power supply.</p>
  </body>
</html>
<?php
system('sudo /usr/sbin/shutdown -h now');
 ?>
