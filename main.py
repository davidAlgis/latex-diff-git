import argparse
import subprocess
import os
import sys


def check_command_exists(command):
    """Check if a command exists in the system's PATH."""
    try:
        if os.name == 'nt':  # Windows
            result = subprocess.run(['where', command],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    encoding='utf-8',
                                    errors='replace')
        else:  # Unix-like systems
            result = subprocess.run(['which', command],
                                    stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE,
                                    encoding='utf-8',
                                    errors='replace')
        return result.returncode == 0
    except Exception as e:
        print(f"Error checking command {command}: {e}", file=sys.stderr)
        return False


def get_repo_root_from_path(path):
    """Retrieve the git repository root for a given file path."""
    file_dir = os.path.dirname(os.path.abspath(path))
    try:
        repo_root = subprocess.check_output(
            ['git', 'rev-parse', '--show-toplevel'],
            cwd=file_dir,
            encoding='utf-8',
            errors='replace').strip()
        return repo_root
    except subprocess.CalledProcessError:
        print(
            f"Error: Could not determine repository root for {path}. "
            "Make sure the file is inside a git repository.",
            file=sys.stderr)
        sys.exit(1)


def get_commit_info(commit_id, repo_root):
    """Retrieve the commit title and ID for debugging output."""
    try:
        commit_title = subprocess.check_output(
            ['git', '-C', repo_root, 'log', '-1', '--format=%s', commit_id],
            encoding='utf-8',
            errors='replace').strip()
        return f'"{commit_title}" ({commit_id})'
    except subprocess.CalledProcessError:
        print(f"Warning: Could not retrieve commit title for {commit_id}.",
              file=sys.stderr)
        return f"(unknown title) ({commit_id})"


def get_file_from_commit(commit_id, file_path, repo_root):
    """Retrieve a file from a specific Git commit in the repository at repo_root."""
    try:
        result = subprocess.run(
            ['git', '-C', repo_root, 'show', f'{commit_id}:{file_path}'],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            encoding='utf-8',
            errors='replace')
        if result.returncode != 0:
            print(f"Error: Could not retrieve file from commit {commit_id}.",
                  file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)
        return result.stdout
    except Exception as e:
        print(f"Error retrieving file from commit {commit_id}: {e}",
              file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Compare two versions of a .tex file using latexdiff.")
    parser.add_argument(
        '-i',
        '--input',
        required=True,
        help="Absolute or relative path of the .tex file to compare.")
    parser.add_argument(
        '-co',
        '--old_commit_id',
        required=True,
        help="The commit ID containing the old version of the file.")
    parser.add_argument(
        '-cn',
        '--new_commit_id',
        required=False,
        default='HEAD',
        help=
        "The commit ID containing the new version of the file. Defaults to HEAD."
    )
    parser.add_argument(
        '-o',
        '--output',
        required=False,
        help="Path for the output diff .tex file. "
        "If not provided, the output is saved near the input file as 'input-diff.tex'."
    )

    args = parser.parse_args()

    # Check for necessary commands.
    if not check_command_exists('latexdiff'):
        print("Error: latexdiff command not found.", file=sys.stderr)
        sys.exit(1)
    if not check_command_exists('git'):
        print("Error: git command not found.", file=sys.stderr)
        sys.exit(1)

    # Deduce the repository root from the input file's location.
    repo_root = get_repo_root_from_path(args.input)
    repo_root_abs = os.path.abspath(repo_root)

    # Compute the absolute and relative path of the input file.
    input_abs = os.path.abspath(args.input)
    relative_input = os.path.relpath(input_abs, repo_root_abs)

    file_full_path = os.path.join(repo_root_abs, relative_input)
    if not os.path.isfile(file_full_path):
        print(
            f"Error: The file {args.input} does not exist in the repository at {repo_root_abs}.",
            file=sys.stderr)
        sys.exit(1)

    # Retrieve commit titles for debug output
    old_commit_info = get_commit_info(args.old_commit_id, repo_root_abs)
    new_commit_info = get_commit_info(args.new_commit_id, repo_root_abs)

    print("\nLatex diff between:")
    print(f"  Old Version -> Commit {old_commit_info}")
    print(f"  New Version -> Commit {new_commit_info}\n")

    # Retrieve the old and new versions of the file from the specified commits.
    old_file_content = get_file_from_commit(args.old_commit_id, relative_input,
                                            repo_root_abs)
    new_file_content = get_file_from_commit(args.new_commit_id, relative_input,
                                            repo_root_abs)

    # Write the file versions to temporary files.
    old_file_path = 'old_version.tex'
    new_file_path = 'new_version.tex'
    try:
        with open(old_file_path, 'w', encoding='utf-8') as old_file:
            old_file.write(old_file_content)
        with open(new_file_path, 'w', encoding='utf-8') as new_file:
            new_file.write(new_file_content)

        print("Applying latex diff...")

        # Run latexdiff to compare the two versions.
        result = subprocess.run(['latexdiff', old_file_path, new_file_path],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                encoding='utf-8',
                                errors='replace')
        if result.returncode != 0:
            print("Error: latexdiff failed.", file=sys.stderr)
            print(result.stderr, file=sys.stderr)
            sys.exit(1)

        # Determine the output path if not provided.
        if not args.output:
            input_dir = os.path.dirname(input_abs)
            base, ext = os.path.splitext(os.path.basename(input_abs))
            args.output = os.path.join(input_dir, f"{base}-diff{ext}")

        # Write the output diff to file.
        with open(args.output, 'w', encoding='utf-8') as outfile:
            outfile.write(result.stdout)

        print(f"Done.")
        print(f"Output is available at '{args.output}'.")

    except Exception as e:
        print(f"Error during processing: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        # Clean up temporary files.
        for temp_file in (old_file_path, new_file_path):
            try:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
            except Exception as cleanup_error:
                print(
                    f"Warning: Could not remove temporary file {temp_file}: {cleanup_error}",
                    file=sys.stderr)
