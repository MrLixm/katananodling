# Katana launcher script

cd ..

KATANA_VERSION="3.6v5"
KATANA_HOME="C:\Program Files\Katana$KATANA_VERSION"
KATANA_TAGLINE="katananodling DEV"

export PATH="$PATH;$KATANA_HOME\bin"
export KATANA_CATALOG_RECT_UPDATE_BUFFER_SIZE=1
export FNLOGGING_CONFIG=".\dev\KatanaResources\log.conf"
#export KATANA_LOGGING_LEVEL_PYTHON="DEBUG"  # custom added in log.conf
#export KATANA_NODLING_NODE_PARAM_DEBUG=1

export KATANA_USER_RESOURCE_DIRECTORY=".\dev\_prefs"
export KATANA_RESOURCES="$KATANA_RESOURCES;.\dev\KatanaResources"

export PYTHONPATH="$PYTHONPATH;..\katananodling"

"$KATANA_HOME\bin\katanaBin.exe"
