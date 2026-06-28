export default function Logo({ size = 32, className = "" }) {
  return (
    <svg
      className={`logo ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <defs>
        <linearGradient id="logo-grad" x1="4" y1="4" x2="36" y2="36" gradientUnits="userSpaceOnUse">
          <stop stopColor="#22d3ee" />
          <stop offset="1" stopColor="#818cf8" />
        </linearGradient>
        <linearGradient id="logo-shine" x1="8" y1="8" x2="32" y2="32" gradientUnits="userSpaceOnUse">
          <stop stopColor="#ffffff" stopOpacity="0.18" />
          <stop offset="1" stopColor="#ffffff" stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="36" height="36" rx="10" fill="#111116" stroke="url(#logo-grad)" strokeWidth="1.5" />
      <rect x="2" y="2" width="36" height="36" rx="10" fill="url(#logo-shine)" />
      <rect x="11" y="12" width="14" height="2" rx="1" fill="#e4e4e7" opacity="0.9" />
      <rect x="11" y="17" width="18" height="2" rx="1" fill="#a1a1aa" />
      <rect x="11" y="22" width="10" height="2" rx="1" fill="#71717a" />
      <circle cx="28" cy="26" r="5" fill="url(#logo-grad)" opacity="0.25" />
      <path
        d="M25.5 26L27.2 27.8L30.8 24"
        stroke="url(#logo-grad)"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <circle cx="8" cy="28" r="2" fill="#22d3ee" opacity="0.6" />
      <circle cx="14" cy="30" r="1.5" fill="#818cf8" opacity="0.5" />
    </svg>
  );
}