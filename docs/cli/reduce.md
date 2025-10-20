# GDM Transformation

## Network Reduction

You can use `reduce` command to perform network reduction is GDM system.

```bash
Usage: gdm reduce [OPTIONS]

Options:
  -g, --gdm-file TEXT          GDM system JSON file path.
  -t, --target-file TEXT       Target GDM system JSON file path.
  -f, --force                  Force delete the target GDM system file if
                               already exists.
  -r, --reducer [three_phase]  Delete target GDM file forcefully if exists.
  -ts, --time-series            Delete target GDM file forcefully if exists.
  --help                       Show this message and exit.

```

Following command converts test.json file to test_reduced.json file including time series data.

```bash
gdm redcue -g 'test.json' -t 'test_reduced.json' -r "three_phase" -ts
```