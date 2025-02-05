# latex-diff-git

This Python script automates the process of comparing two versions of a `.tex` file stored in a Git repository using `latexdiff`. It retrieves two versions of the file from different commits, runs `latexdiff`, and saves the result as a new `.tex` file highlighting the differences.

## Installation

Before running the script, ensure you have the necessary dependencies installed. You need:

- Python 3.6 or newer
- `git` installed and available in your system’s PATH
- `latexdiff` installed and available in your system’s PATH (available via TeX Live or MiKTeX)

## Usage

Ensure that the `.tex` file you want to compare is inside a Git repository. Run the script from the command line with the desired options:

```sh
python main.py [options]
```

## Options

- `-i`, `--input <file>`: **(Required)** The `.tex` file to compare. This file must be tracked in a Git repository.
  
- `-co`, `--old_commit_id <commit_id>`: **(Required)** The commit ID corresponding to the old version of the file.

- `-cn`, `--new_commit_id <commit_id>`: The commit ID for the new version of the file. Defaults to `HEAD` (latest commit in the repository).

- `-o`, `--output <file>`: The output `.tex` file that will contain the `latexdiff` result. If not specified, the output file is saved in the same directory as the input file with the name `<input>-diff.tex`.

## Example

To compare a `.tex` file (`paper.tex`) between an old commit and the latest commit:

```sh
python main.py -i "paper.tex" -co "98700d80c59d35da6029030412cf64803ea9a5e5"
```

This will generate `paper-diff.tex` in the same directory as `paper.tex`.
