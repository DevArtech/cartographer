/**
 * Commitlint configuration for semantic versioning
 * 
 * Commit message format: <type>(<scope>): <subject>
 * 
 * Types that trigger AUTOMATIC version bumps on commit:
 *   - feat:     New feature → MINOR version bump (0.x.0)
 *   - fix:      Bug fix → PATCH version bump (0.0.x)
 *   - perf:     Performance improvement → PATCH version bump (0.0.x)
 * 
 * Types that do NOT trigger version bumps:
 *   - docs:     Documentation only
 *   - style:    Code style (formatting, semicolons, etc.)
 *   - refactor: Code refactoring (no feature/fix)
 *   - test:     Adding/updating tests
 *   - chore:    Maintenance tasks
 *   - ci:       CI/CD changes
 *   - build:    Build system changes
 *   - revert:   Reverting previous commits
 *   - lint:     Linting fixes
 *   - config:   Configuration file changes
 *   - wip:      Work in progress
 * 
 * Breaking changes:
 *   Add "BREAKING CHANGE:" in the commit body or "!" after type
 *   Example: feat!: new API endpoint
 *   Use "npm run release:major" for major version bumps
 * 
 * Examples:
 *   feat(auth): add OAuth2 support         → bumps minor version
 *   fix(network): resolve connection issue → bumps patch version
 *   perf(db): optimize queries             → bumps patch version
 *   docs: update README                    → no version bump
 *   refactor(backend): simplify code       → no version bump
 */

module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // Type must be one of the allowed values
    'type-enum': [
      2,
      'always',
      [
        'feat',     // New feature → MINOR version bump
        'fix',      // Bug fix → PATCH version bump
        'perf',     // Performance improvements → PATCH version bump
        'docs',     // Documentation only (no version bump)
        'style',    // Code style changes (no version bump)
        'refactor', // Code refactoring (no version bump)
        'test',     // Adding or updating tests (no version bump)
        'chore',    // Maintenance tasks (no version bump)
        'ci',       // CI/CD configuration changes (no version bump)
        'build',    // Build system changes (no version bump)
        'revert',   // Reverting a previous commit (no version bump)
        'lint',     // Linting fixes (no version bump)
        'config',   // Configuration file changes (no version bump)
        'wip'       // Work in progress (no version bump)
      ]
    ],
    // Type must be lowercase
    'type-case': [2, 'always', 'lower-case'],
    // Type cannot be empty
    'type-empty': [2, 'never'],
    // Scope should be lowercase if provided
    'scope-case': [2, 'always', 'lower-case'],
    // Subject cannot be empty
    'subject-empty': [2, 'never'],
    // Subject should not end with a period
    'subject-full-stop': [2, 'never', '.'],
    // Subject should be sentence case or lower case
    'subject-case': [
      2,
      'never',
      ['sentence-case', 'start-case', 'pascal-case', 'upper-case']
    ],
    // Header (type + scope + subject) max length
    'header-max-length': [2, 'always', 100],
    // Body max line length
    'body-max-line-length': [2, 'always', 200],
    // Footer max line length
    'footer-max-line-length': [2, 'always', 200]
  },
  // Help messages shown when validation fails
  helpUrl: 'https://www.conventionalcommits.org/'
};

