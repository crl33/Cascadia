// Minimal ESLint: TypeScript recommended + React hooks. Import boundaries are enforced by
// no-restricted-imports: panels/, state/, api/ and interactions/ never import the renderer.
import js from '@eslint/js';
import tseslint from 'typescript-eslint';
import reactHooks from 'eslint-plugin-react-hooks';

const rendererBoundary = {
  files: ['src/panels/**', 'src/state/**', 'src/api/**', 'src/interactions/**', 'src/app/**', 'src/timeline/**'],
  rules: {
    'no-restricted-imports': [
      'error',
      { paths: [{ name: 'cesium', message: 'Only scene/, camera/ and layers/ may import the renderer.' }] },
    ],
  },
};

export default tseslint.config(
  { ignores: ['dist/**', 'src/contracts/generated.ts'] },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  { plugins: { 'react-hooks': reactHooks }, rules: { ...reactHooks.configs.recommended.rules } },
  { rules: { '@typescript-eslint/no-unused-vars': ['error', { argsIgnorePattern: '^_' }] } },
  rendererBoundary,
);
