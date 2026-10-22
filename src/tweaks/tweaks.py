from .tweak_names import TweakID
from .tweak_classes import MobileGestaltTweak, MobileGestaltMultiTweak, MobileGestaltPickerTweak, FeatureFlagTweak, BasicPlistTweak, AdvancedPlistTweak, RdarFixTweak, NullifyFileTweak
from .eligibility_tweak import EligibilityTweak, AITweak, BookRestoreFileTweak
from .basic_plist_locations import FileLocation
    
tweaks = {
    ## Creating the folders for BookRestore
    TweakID.CreateBRFolders: BookRestoreFileTweak()
}
