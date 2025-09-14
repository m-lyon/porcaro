import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import reactRefresh from 'eslint-plugin-react-refresh';
import tseslint from 'typescript-eslint';
import prettier from 'eslint-config-prettier';
import eslintImport from 'eslint-plugin-import';
import eslintImportLineSorter from 'eslint-plugin-import-line-sorter';

export default tseslint.config(
    {
        ignores: ['dist'],
    },
    js.configs.recommended,
    ...tseslint.configs.recommended,
    prettier,
    {
        files: ['**/*.{ts,tsx,js,jsx}'],
        plugins: {
            'react-hooks': reactHooks,
            'react-refresh': reactRefresh,
            import: eslintImport,
            'import-line-sorter': eslintImportLineSorter,
        },
        languageOptions: {
            ecmaVersion: 2020,
            globals: globals.browser,
        },
        rules: {
            ...reactHooks.configs.recommended.rules,
            'react-refresh/only-export-components': ['warn', { allowConstantExport: true }],
            'import/no-duplicates': 'off',
            'import/no-unresolved': 'off',
            'import/order': [
                'warn',
                {
                    pathGroups: [
                        {
                            pattern: '@recipe/**',
                            group: 'external',
                            position: 'after',
                        },
                    ],
                    pathGroupsExcludedImportTypes: ['@recipe/**'],
                    groups: [
                        'builtin',
                        'external',
                        'internal',
                        ['sibling', 'parent'],
                        'index',
                        'unknown',
                    ],
                    'newlines-between': 'always',
                },
            ],
            'import-line-sorter/sort-imports': 'warn',
            'import-line-sorter/no-multiline-imports': 'warn',
            'react-hooks/rules-of-hooks': 'error',
            'react-hooks/exhaustive-deps': 'warn',
        },
    }
);
