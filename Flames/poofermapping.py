''' pooferMappings is an object containing poofer names as attributes, where each 
attribute value is a string of 3 digits that translate to the poofer's address on the 
poofer control boards.  The first and second digits is the board number in hexadecimal, 
and the third digit is the channel on that board (there are 8 channels per board).
The required attribute names are:
		NN,NW,NE,NT,EN,EE,ES,ET,SE,SS,SW,ST,WS,WW,WN,WT,TN,TE,TS,TW,TT,BN,BE,BS,BW
and the addresses depend on the number of channels we use on each poofer board. 
'''

mappings = {}
mappings["NN"]="010"
mappings['NW']="011"
mappings['NE']="012"
mappings['NT']="013"
mappings['EN']="014"
mappings['EE']="015"
mappings['ES']="016"
mappings['ET']="020"
mappings['SE']="021"
mappings['SS']="022"
mappings['SW']="023"
mappings['ST']="024"
mappings['WS']="026"
mappings['WW']="030"
mappings['WN']="031"
mappings['WT']="032"
mappings['TN']="033"
mappings['TE']="034"
mappings['TS']="035"
mappings['TW']="040"
mappings['TT']="041"
mappings['BN']="042"
mappings['BE']="043"
mappings['BS']="044"
mappings['BW']="045"