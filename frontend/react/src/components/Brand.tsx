import s from "./Brand.module.css";

export function Brand({
  wordmark = true,
  large = false,
}: {
  wordmark?: boolean;
  large?: boolean;
}) {
  return (
    <span className={`${s.brand} ${large ? s.large : ""}`}>
      <img
        src="/branding/upstream-mark.svg"
        width={large ? 44 : 32}
        height={large ? 44 : 32}
        alt=""
        aria-hidden="true"
      />
      {wordmark && <span>Upstream</span>}
    </span>
  );
}
