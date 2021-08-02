# Network:
net-max-write-queue 50000
net-want-threads #f

# MessageDirector:
messagedirector-address 0.0.0.0
messagedirector-port 7100
messagedirector-message-timeout 15.0

# ClientAgent:
clientagent-address 0.0.0.0
clientagent-port 6667
clientagent-connect-address 127.0.0.1
clientagent-connect-port 7100
clientagent-channel 1000
clientagent-max-channels 1000001000
clientagent-min-channels 1000000000
clientagent-dbm-filename databases/database.dbm
clientagent-dbm-mode c
clientagent-version dev
clientagent-hash-val 0

# StateServer:
stateserver-connect-address 127.0.0.1
stateserver-connect-port 7100
stateserver-channel 1001

# Database:
database-connect-address 127.0.0.1
database-connect-port 7100
database-channel 1002
database-directory databases/json
database-extension .json
database-max-channels 199999999
database-min-channels 100000000

# DClass:
#dc-multiple-inheritance #t
#dc-sort-virtual-inheritance #t
#dc-sort-inheritance-by-file #f


# DNA:
DNA_LENGTH 15
DNA_FIRST_CHAR t

DNA_MAX_ARM_COLOR 26 
DNA_MAX_FEMALE_SHIRT_COLOR 28
DNA_MAX_FEMALE_SHIRT_INDEX 23 
DNA_MAX_FEMALE_SHORTS_COLOR 28
DNA_MAX_FEMALE_SHORTS_INDEX 10
DNA_MAX_FEMALE_SLEEVE_COLOR 28
DNA_MAX_FEMALE_SLEEVE_INDEX 14
DNA_MAX_GENDER_INDEX 2 
DNA_MAX_GLOVE_COLOR 1 
DNA_MAX_HEAD_COLOR 26 
DNA_MAX_HEAD_INDEX 34
DNA_MAX_LEG_COLOR 26 
DNA_MAX_LEG_INDEX 3 
DNA_MAX_MALE_SHIRT_COLOR 28
DNA_MAX_MALE_SHIRT_INDEX 23
DNA_MAX_MALE_SHORTS_COLOR 28
DNA_MAX_MALE_SHORTS_INDEX 8 
DNA_MAX_MALE_SLEEVE_COLOR 28
DNA_MAX_MALE_SLEEVE_INDEX 14
DNA_MAX_TORSO_INDEX 9 