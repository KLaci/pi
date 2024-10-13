import btfpy

def callback(node,operation,ctic_index):
  if operation == btfpy.LE_CONNECT:
    print("Connected")
  elif operation == btfpy.LE_DISCONNECT:
    print("Disconnected")
    return(btfpy.SERVER_EXIT)
  return(btfpy.SERVER_CONTINUE)

if btfpy.Init_blue("devices.txt") == 0:
  exit(0)

print("Use 1st entry in devices.txt (My Pi) for")
print("this device to define LE characteristics")
  # Set My data (index 1) value
btfpy.Write_ctic(btfpy.Localnode(),1,"Hello world",0)

    # CONNECTION/PAIRING PROBLEMS?
    # See section 3-7-1 Random address alternative setup

btfpy.Le_server(callback,0)
btfpy.Close_all()
