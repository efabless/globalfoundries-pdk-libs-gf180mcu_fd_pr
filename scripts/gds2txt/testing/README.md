# GDS/TXT Conversion Testing Documentation

Explains how to test the converter.

## Folder Structure

```text
📦testing
 ┣ 📦testcases
 ┣ 📜test_conversion.py
 ┗ 📜xor.drc
 ```

## Explaination

The `test_conversion.py` script takes all gds files in `testcases/` and convert them to text files then bring back all gds files by converting them from text files. Reports will be generated by `xor.drc` and finally analyzed to check the correctness of conversion.

## Usage

```bash
    python3 test_conversion.py
```

## **Regression Outputs**

A run folder will contain:

- The text files. `<name>.txt`
- The gds files after conversion. `<name>_o.gds`
- A gds file of XOR process `<name>_r.gds`
- A layer database of the XOR file. `<name>_xor.lyrdb`