import './globals.css'

export const metadata = {
  title: '양봉클럽',
  description: 'LIVE Market & News',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko">
      <body>{children}</body>
    </html>
  )
}
