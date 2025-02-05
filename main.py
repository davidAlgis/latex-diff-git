import argparse
import subprocess
import os
import sys


def check_command_exists(command):
    """Check if a command exists in the system's PATH."""
    return subprocess.run(['which', command],
                          stdout=subprocess.PIPE,
                          stderr=subprocess.PIPE).returncode == 0


def get_file_from_commit(commit_id, file_path):
    """Retrieve a file from a specific Git commit."""
    try:
        result = subprocess.run(['git', 'show', f'{commit_id}:{file_path}'],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        if result.returncode != 0:
            print(f"Error: Could not retrieve file from commit {commit_id}.",
                  file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
        return result.stdout
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Compare two versions of a .tex file using latexdiff.')
    parser.add_argument('-t',
                        '--tex_file',
                        required=True,
                        help='The name of the .tex file to compare.')
    parser.add_argument(
        '-o',
        '--old_commit_id',
        required=True,
        help='The commit ID containing the old version of the file.')
    parser.add_argument(
        '-n',
        '--new_commit_id',
        required=True,
        help='The commit ID containing the new version of the file.')

    args = parser.parse_args()

    # Check if necessary commands are available
    if not check_command_exists('latexdiff'):
        print("Error: latexdiff command not found.", file=sys.stderr)
        sys.exit(1)

    if not check_command_exists('git'):
        print("Error: git command not found.", file=sys.stderr)
        sys.exit(1)

    # Check if the .tex file exists in the repository
    if not os.path.isfile(args.tex_file):
        print(
            f"Error: The file {args.tex_file} does not exist in the repository.",
            file=sys.stderr)
        sys.exit(1)

    # Retrieve the old and new versions of the file
    old_file_content = get_file_from_commit(args.old_commit_id, args.tex_file)
    new_file_content = get_file_from_commit(args.new_commit_id, args.tex_file)

    # Write the old and new file contents to temporary files
    old_file_path = 'old_version.tex'
    new_file_path = 'new_version.tex'

    with open(old_file_path, 'w') as old_file:
        old_file.write(old_file_content)

    with open(new_file_path, 'w') as new_file:
        new_file.write(new_file_content)

    # Run latexdiff to compare the two files
    try:
        result = subprocess.run(['latexdiff', old_file_path, new_file_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                text=True)
        if result.returncode != 0:
            print(f"Error: latexdiff failed.", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
        print(result.stdout)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up temporary files
        os.remove(old_file_path)
        os.remove(new_file_path)


if __name__ == '__main__':
    main()
