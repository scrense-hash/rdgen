import os
import re

from django import forms
from PIL import Image

# App/company names are interpolated into single/double-quoted bash sed
# scripts in every generator workflow: & \ | corrupt the substitution
# silently, ' " $ ` break shell quoting, CR/LF break sed addressing.
UNSAFE_NAME_CHARS = re.compile(r'[&\\|\'"$`\r\n]')

# Build targets offered per platform. The first entry of each list is the
# default, so a client that asks for nothing still gets a usable package.
# Keep the keys in sync with GenerateForm.platform choices and with the
# `formats` / `arches` gating in the generator workflows.
PLATFORM_FORMATS = {
    'windows': [('exe', 'EXE installer'), ('msi', 'MSI installer')],
    'windows-x86': [('exe', 'EXE installer')],
    'linux': [
        ('deb', 'DEB (Debian/Ubuntu)'),
        ('drm', 'DEB unattended-wayland (DRM capture, lock/login screen)'),
        ('rpm', 'RPM (Fedora)'),
        ('suse', 'RPM (openSUSE)'),
        ('pkg', 'Arch Linux (pkg.tar.zst)'),
        ('appimage', 'AppImage'),
        ('flatpak', 'Flatpak'),
    ],
    'android': [('apk', 'APK')],
    'macos': [('dmg', 'DMG')],
}

# Optional prefill for the web form: DEFAULT_<NAME> in the environment seeds
# the matching field, so a single-user deployment does not retype the same
# values on every build. Only the web form is affected; the JSON API still
# takes exactly what the caller sends.
BOOL_FORM_FIELDS = {
    'delayFix', 'denyLan', 'enableDirectIP', 'autoClose', 'enableKeyboard',
    'enableClipboard', 'enableFileTransfer', 'enableAudio', 'enableTCP',
    'enableRemoteRestart', 'enableRecording', 'enableBlockingInput',
    'enableRemoteModi', 'hidecm', 'enablePrinter', 'enableCamera',
    'enableTerminal', 'removeWallpaper', 'xOffline', 'removeNewVersionNotif',
    'enableCheckUpdate',
}
LIST_FORM_FIELDS = {'formats', 'arches'}

DEFAULT_ENV_FIELDS = {
    'PLATFORM': 'platform',
    'VERSION': 'version',
    'EXENAME': 'exename',
    'SERVER': 'serverIP',
    'SERVER_PORT': 'serverPort',
    'APISERVER': 'apiServer',
    'KEY': 'key',
    'PASSWORD': 'permanentPassword',
    'DIRECTION': 'direction',
    'INSTALLATION': 'installation',
    'SETTINGS': 'settings',
    'PASS_APPROVE_MODE': 'passApproveMode',
    'PERMISSIONS_DORO': 'permissionsDorO',
    'PERMISSIONS_TYPE': 'permissionsType',
    'THEME': 'theme',
    'THEME_DORO': 'themeDorO',
    'COMPNAME': 'compname',
    'HIDECM': 'hidecm',
    'DENYLAN': 'denyLan',
    'FORMATS': 'formats',
    'ARCHES': 'arches',
    'ENABLE_KEYBOARD': 'enableKeyboard',
    'ENABLE_CLIPBOARD': 'enableClipboard',
    'ENABLE_FILE_TRANSFER': 'enableFileTransfer',
    'ENABLE_AUDIO': 'enableAudio',
    'ENABLE_TCP': 'enableTCP',
    'ENABLE_REMOTE_RESTART': 'enableRemoteRestart',
    'ENABLE_RECORDING': 'enableRecording',
    'ENABLE_BLOCKING_INPUT': 'enableBlockingInput',
    'ENABLE_REMOTE_MODI': 'enableRemoteModi',
    'ENABLE_PRINTER': 'enablePrinter',
    'ENABLE_CAMERA': 'enableCamera',
    'ENABLE_TERMINAL': 'enableTerminal',
    'ENABLE_CHECK_UPDATE': 'enableCheckUpdate',
}


def _env_bool(value):
    return str(value).strip().lower() in ('1', 'true', 'yes', 'y', 'on')


def form_initial():
    """Initial values for GenerateForm, taken from DEFAULT_* env vars."""
    initial = {}
    for env_name, field in DEFAULT_ENV_FIELDS.items():
        raw = os.environ.get('DEFAULT_' + env_name)
        if raw is None or raw.strip() == '':
            continue
        if field in LIST_FORM_FIELDS:
            initial[field] = [v.strip() for v in raw.split(',') if v.strip()]
        elif field in BOOL_FORM_FIELDS:
            initial[field] = _env_bool(raw)
        else:
            initial[field] = raw.strip()
    return initial


PLATFORM_ARCHES = {
    'windows': ['x86_64'],
    'windows-x86': ['x86'],
    'linux': ['x86_64', 'aarch64'],
    'android': ['aarch64', 'x86_64', 'armv7'],
    'macos': ['x86_64', 'aarch64'],
}


def platform_format_codes(platform):
    return [code for code, _ in PLATFORM_FORMATS.get(platform, [])]


def normalize_selection(values, allowed, default=None):
    """Keep only values the platform supports; fall back to the defaults.

    Accepts a list (web form) or a comma separated string (JSON API), so the
    same helper works for both callers.
    """
    if isinstance(values, str):
        values = [v.strip() for v in values.split(',')]
    values = [v for v in (values or []) if v in allowed]
    if not values:
        values = list(default if default is not None else allowed)
    return values

class GenerateForm(forms.Form):
    sh_secret_field = forms.CharField(required=False)
    #Platform
    platform = forms.ChoiceField(choices=[('windows','Windows 64Bit'),('windows-x86','Windows 32Bit'),('linux','Linux'),('android','Android'),('macos','macOS')], initial='windows')
    version = forms.ChoiceField(choices=[('master','nightly'),('1.5.0','1.5.0'),('1.4.9','1.4.9'),('1.4.8','1.4.8'),('1.4.7','1.4.7'),('1.4.6','1.4.6'),('1.4.5','1.4.5'),('1.4.4','1.4.4'),('1.4.3','1.4.3'),('1.4.2','1.4.2'),('1.4.1','1.4.1'),('1.4.0','1.4.0')], initial='1.5.0')
    help_text="'master' is the development version (nightly build) with the latest features but may be less stable"
    delayFix = forms.BooleanField(initial=True, required=False)

    #Build targets (which packages/architectures to produce for the platform)
    formats = forms.MultipleChoiceField(
        label="Formats to build",
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=list(dict.fromkeys(
            (code, label) for choices in PLATFORM_FORMATS.values() for code, label in choices
        )),
    )
    arches = forms.MultipleChoiceField(
        label="Architectures to build",
        required=False,
        widget=forms.CheckboxSelectMultiple,
        choices=list(dict.fromkeys(
            (arch, arch) for arches in PLATFORM_ARCHES.values() for arch in arches
        )),
    )

    #General
    exename = forms.CharField(label="Name for EXE file", required=True)
    direction = forms.ChoiceField(widget=forms.RadioSelect, choices=[
        ('incoming', 'Incoming Only'),
        ('outgoing', 'Outgoing Only'),
        ('both', 'Bidirectional')
    ], initial='both')
    installation = forms.ChoiceField(label="Disable Installation", choices=[
        ('installationY', 'No, enable installation'),
        ('installationN', 'Yes, DISABLE installation')
    ], initial='installationY')
    settings = forms.ChoiceField(label="Disable Settings", choices=[
        ('settingsY', 'No, enable settings'),
        ('settingsN', 'Yes, DISABLE settings')
    ], initial='settingsY')
    androidappid = forms.CharField(label="Custom Android App ID (replaces 'com.carriez.flutter_hbb')", required=False)

    #Custom Server
    serverIP = forms.CharField(label="Host", required=False)
    serverPort = forms.CharField(label="Port", required=False)
    apiServer = forms.CharField(label="API Server", required=False)
    key = forms.CharField(label="Key", required=False)
    urlLink = forms.CharField(label="Custom URL for links", required=False)
    downloadLink = forms.CharField(label="Custom URL for downloading new versions", required=False)
    compname = forms.CharField(label="Company name",required=False)

    #Visual
    iconfile = forms.FileField(label="Custom App Icon (in .png format)", required=False, widget=forms.FileInput(attrs={'accept': 'image/png'}))
    logofile = forms.FileField(label="Custom App Logo (in .png format)", required=False, widget=forms.FileInput(attrs={'accept': 'image/png'}))
    privacyfile = forms.FileField(label="Custom privacy screen (in .png format)", required=False, widget=forms.FileInput(attrs={'accept': 'image/png'}))
    iconbase64 = forms.CharField(required=False)
    logobase64 = forms.CharField(required=False)
    privacybase64 = forms.CharField(required=False)
    theme = forms.ChoiceField(choices=[
        ('light', 'Light'),
        ('dark', 'Dark'),
        ('system', 'Follow System')
    ], initial='system')
    themeDorO = forms.ChoiceField(choices=[('default', 'Default'),('override', 'Override')], initial='default')

    #Security
    passApproveMode = forms.ChoiceField(choices=[('password','Accept sessions via password'),('click','Accept sessions via click'),('password-click','Accepts sessions via both')],initial='password-click')
    # render_value so a DEFAULT_PASSWORD from .env actually shows up in the
    # field: Django omits the value of a password input by default. The page is
    # behind basic auth, and the value is only as exposed as the prefilled
    # field itself.
    permanentPassword = forms.CharField(widget=forms.PasswordInput(render_value=True), required=False)
    #runasadmin = forms.ChoiceField(choices=[('false','No'),('true','Yes')], initial='false')
    denyLan = forms.BooleanField(initial=False, required=False)
    enableDirectIP = forms.BooleanField(initial=False, required=False)
    #ipWhitelist = forms.BooleanField(initial=False, required=False)
    autoClose = forms.BooleanField(initial=False, required=False)

    #Permissions
    permissionsDorO = forms.ChoiceField(choices=[('default', 'Default'),('override', 'Override')], initial='default')
    permissionsType = forms.ChoiceField(choices=[('custom', 'Custom'),('full', 'Full Access'),('view','Screen share')], initial='custom')
    enableKeyboard =  forms.BooleanField(initial=True, required=False)
    enableClipboard = forms.BooleanField(initial=True, required=False)
    enableFileTransfer = forms.BooleanField(initial=True, required=False)
    enableAudio = forms.BooleanField(initial=True, required=False)
    enableTCP = forms.BooleanField(initial=True, required=False)
    enableRemoteRestart = forms.BooleanField(initial=True, required=False)
    enableRecording = forms.BooleanField(initial=True, required=False)
    enableBlockingInput = forms.BooleanField(initial=True, required=False)
    enableRemoteModi = forms.BooleanField(initial=False, required=False)
    hidecm = forms.BooleanField(initial=False, required=False)
    enablePrinter = forms.BooleanField(initial=True, required=False)
    enableCamera = forms.BooleanField(initial=True, required=False)
    enableTerminal = forms.BooleanField(initial=True, required=False)

    #Other
    removeWallpaper = forms.BooleanField(initial=True, required=False)

    defaultManual = forms.CharField(widget=forms.Textarea, required=False)
    overrideManual = forms.CharField(widget=forms.Textarea, required=False)

    #custom added features
    xOffline = forms.BooleanField(initial=False, required=False)
    removeNewVersionNotif = forms.BooleanField(initial=False, required=False)
    # Writes enable-check-update; the workflow's removeNewVersionNotif patch
    # only guts the updater, it leaves this setting on in the client UI.
    enableCheckUpdate = forms.BooleanField(initial=False, required=False)

    def clean_iconfile(self):
        print("checking icon")
        image = self.cleaned_data['iconfile']
        if image:
            try:
                # Open the image using Pillow
                img = Image.open(image)

                # Check if the image is a PNG (optional, but good practice)
                if img.format != 'PNG':
                    raise forms.ValidationError("Only PNG images are allowed.")

                # Get image dimensions
                width, height = img.size

                # Check for square dimensions
                if width != height:
                    raise forms.ValidationError("Custom App Icon dimensions must be square.")
                
                return image
            except OSError:  # Handle cases where the uploaded file is not a valid image
                raise forms.ValidationError("Invalid icon file.")
            except Exception as e: # Catch any other image processing errors
                raise forms.ValidationError(f"Error processing icon: {e}")

    def _reject_unsafe_name_chars(self, field):
        value = self.cleaned_data.get(field, '')
        if value and UNSAFE_NAME_CHARS.search(value):
            raise forms.ValidationError(
                "Contains characters unsupported in build scripts "
                "(& \\ | ' \" $ `, newlines)."
            )
        return value

    def clean_compname(self):
        return self._reject_unsafe_name_chars('compname')

    def clean(self):
        cleaned_data = super().clean()
        platform = cleaned_data.get('platform')
        # Ignore boxes that belong to another platform (the form shows every
        # platform's targets, only the selected one is submitted) and fall
        # back to all targets of that platform when nothing is ticked.
        cleaned_data['formats'] = normalize_selection(
            cleaned_data.get('formats'),
            platform_format_codes(platform),
        )
        cleaned_data['arches'] = normalize_selection(
            cleaned_data.get('arches'),
            PLATFORM_ARCHES.get(platform, []),
        )
        return cleaned_data
