# PowerShell script to rewrite commit history
param([string]$targetCommit, [string]$newCommit)

Write-Host "Rewriting commit history to replace $targetCommit with $newCommit"

# Set git editor to avoid interactive mode
$env:GIT_EDITOR = "echo"

# Get the current branch
$currentBranch = git branch --show-current
Write-Host "Current branch: $currentBranch"

# Find the parent of the target commit
$parentCommit = git show --format="%P" --no-patch $targetCommit
Write-Host "Parent commit: $parentCommit"

# Create a new branch from the parent
$tempBranch = "temp-rewrite-$(Get-Random)"
Write-Host "Creating temporary branch: $tempBranch"
git checkout -b $tempBranch $parentCommit

# Cherry-pick the new commit
Write-Host "Cherry-picking the cleaned commit..."
git cherry-pick $newCommit

# Get the new commit hash
$newCommitHash = git rev-parse HEAD
Write-Host "New commit hash: $newCommitHash"

# Now rebase the original branch onto this new commit
Write-Host "Rebasing original branch..."
git checkout $currentBranch

# Find commits after the target commit
$commitsAfter = git rev-list --reverse $targetCommit..HEAD
Write-Host "Commits after target: $commitsAfter"

# Reset to the new commit
git reset --hard $newCommitHash

# Cherry-pick the remaining commits
foreach ($commit in $commitsAfter) {
    if ($commit -ne $newCommit) {
        Write-Host "Cherry-picking commit: $commit"
        git cherry-pick $commit
    }
}

# Clean up temporary branch
git branch -D $tempBranch

Write-Host "Commit history rewritten successfully!"
Write-Host "Original commit $targetCommit has been replaced with $newCommitHash"
