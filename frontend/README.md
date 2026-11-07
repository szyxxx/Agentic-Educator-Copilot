This is a [Next.js](https://nextjs.org) project bootstrapped with [`create-next-app`](https://nextjs.org/docs/app/api-reference/cli/create-next-app).

## Getting Started

First, run the development server:

```bash
npm run dev
# or
yarn dev
# or
pnpm dev
# or
bun dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser to see the result.

You can start editing the page by modifying `app/page.tsx`. The page auto-updates as you edit the file.

This project uses [`next/font`](https://nextjs.org/docs/app/building-your-application/optimizing/fonts) to automatically optimize and load [Geist](https://vercel.com/font), a new font family for Vercel.

## Learn More

To learn more about Next.js, take a look at the following resources:

- [Next.js Documentation](https://nextjs.org/docs) - learn about Next.js features and API.
- [Learn Next.js](https://nextjs.org/learn) - an interactive Next.js tutorial.

You can check out [the Next.js GitHub repository](https://github.com/vercel/next.js) - your feedback and contributions are welcome!

## Deploy on Vercel

The easiest way to deploy your Next.js app is to use the [Vercel Platform](https://vercel.com/new?utm_medium=default-template&filter=next.js&utm_source=create-next-app&utm_campaign=create-next-app-readme) from the creators of Next.js.

Check out our [Next.js deployment documentation](https://nextjs.org/docs/app/building-your-application/deploying) for more details.


## Pemutakhiran keamanan dependensi

Next.js dan eslint-config-next memakai lini 16.4.5, dengan React/ReactDOM tetap
pada major 19. Gunakan `npm ci` agar versi pada lockfile terpasang persis.
Override `@tailwindcss/typography > postcss-selector-parser` memilih patch
6.1.5 pada major 6 karena typography 0.5.20 masih mengunci versi 6.0.10 yang
terdampak advisori DoS parser CSS. Jangan menghapus override sebelum upstream
memperbaiki dependensinya dan audit ulang memastikan jalur tersebut aman.

Rantai dev `eslint-config-next > typescript-eslint > typescript-estree` masih
memakai minimatch 10.2.6. Perbaikan GHSA-g3hv-75wg-m249 tersedia mulai 11.0.1;
upgrade major transitif itu tidak dipaksakan. Glob project/config lint harus
berasal dari sumber yang dipercaya. Tidak ada jalur HTTP aplikasi yang
memanggil tooling ESLint ini; periksa `npm audit` dan `npm audit --omit=dev`
secara terpisah saat memperbarui dependensi.

Navigasi setelah login/logout atau sesi berakhir sengaja memuat dokumen baru
melalui `session-navigation.ts`, agar cache klien/RSC dari sesi sebelumnya
terbuang. Pertahankan batas cookie, Origin, dan proxy API satu origin.

Override `react-markdown > hast-util-to-jsx-runtime` mempertahankan 2.3.6
agar rantai `style-to-js`/`style-to-object` tetap pada major 1 yang sudah dipakai.
Patch parent 2.3.7 mengganti dependensinya ke style-to-object major 2; pembaruan
major transitif itu ditunda sesuai batas pemutakhiran ini.
