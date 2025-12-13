# product_map.py
# Keep the provided CPE matchstrings; keyword is retained as a safe fallback.
PRODUCTS = {
    "all": {
        "label": "All products",
        "keyword": None,
        "cpe": None
    },
    "tenda": {
        "label": "Tenda",
        "keyword": "tenda",
        "cpe": "cpe:2.3:*:tenda:*:*:*:*:*:*:*:*:*"
    },
    "tplink": {
        "label": "TP-Link",
        "keyword": "tp-link",
        "cpe": "cpe:2.3:*:tp-link:*:*:*:*:*:*:*:*:*"
    },
    "synology": {
        "label": "Synology",
        "keyword": "synology",
        "cpe": "cpe:2.3:*:synology:*:*:*:*:*:*:*:*:*"
    },
    "chrome": {
        "label": "Google Chrome",
        "keyword": "google chrome",
        "cpe": "cpe:2.3:*:google:chrome:*:*:*:*:*:*:*:*"
    },
    "linux": {
        "label": "Linux kernel (generic)",
        "keyword": "linux kernel",
        "cpe": "cpe:2.3:*:linux:linux_kernel:*:*:*:*:*:*:*:*"
    },
    "redhat": {
        "label": "Red Hat (Linux kernel)",
        "keyword": "red hat",
        "cpe": "cpe:2.3:*:linux:linux_kernel:*:*:*:*:*:*:*:*"
    },
    "suse": {
        "label": "SUSE Linux",
        "keyword": "suse",
        "cpe": "cpe:2.3:*:suse:*:*:*:*:*:*:*:*:*"
    },
    "windows": {
        "label": "Microsoft Windows",
        "keyword": "microsoft windows",
        "cpe": None
    },
    "vmware_workstation": {
        "label": "VMware Workstation",
        "keyword": "vmware workstation",
        "cpe": "cpe:2.3:*:vmware:workstation:*:*:*:*:*:*:*:*"
    },
    "vmware_esxi": {
        "label": "VMware ESXi",
        "keyword": "vmware esxi",
        "cpe": "cpe:2.3:*:vmware:esxi:*:*:*:*:*:*:*:*"
    }
}