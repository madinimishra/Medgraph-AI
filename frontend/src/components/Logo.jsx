export default function Logo({ size = 32, className = "" }) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      className={className}
      aria-label="MedGraph AI logo"
    >
      <defs>
        <linearGradient id="logo-grad" x1="0" y1="0" x2="40" y2="40" gradientUnits="userSpaceOnUse">
          <stop offset="0" stopColor="#5b8def" />
          <stop offset="1" stopColor="#7c5cff" />
        </linearGradient>
      </defs>
      <line x1="9" y1="31" x2="20" y2="10" stroke="url(#logo-grad)" strokeWidth="2" strokeLinecap="round" />
      <line x1="31" y1="31" x2="20" y2="10" stroke="url(#logo-grad)" strokeWidth="2" strokeLinecap="round" />
      <line x1="9" y1="31" x2="31" y2="31" stroke="url(#logo-grad)" strokeWidth="2" strokeLinecap="round" />
      <circle cx="9" cy="31" r="4.5" fill="url(#logo-grad)" />
      <circle cx="31" cy="31" r="4.5" fill="url(#logo-grad)" />
      <circle cx="20" cy="10" r="6" fill="url(#logo-grad)" />
      <path d="M20 6.5v7M16.5 10h7" stroke="#0f1420" strokeWidth="1.6" strokeLinecap="round" />
    </svg>
  );
}
