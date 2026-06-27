export default function Logo({ size = 24, className = "" }) {
  return (
    <svg
      className={`logo ${className}`.trim()}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true"
    >
      <rect x="2" y="2" width="20" height="20" rx="3" fill="#1a1a1a" />
      <rect x="6" y="7" width="9" height="1.5" rx="0.75" fill="#fff" />
      <rect x="6" y="11" width="12" height="1.5" rx="0.75" fill="#fff" />
      <rect x="6" y="15" width="7" height="1.5" rx="0.75" fill="#fff" />
      <path
        d="M14.5 14.5L16.5 16.5L20 12.5"
        stroke="#4ade80"
        strokeWidth="1.75"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}