import s from "./Brand.module.css";

/**
 * Render the decorative Upstream symbol with an optional visible wordmark.
 *
 * When wordmark is false, the enclosing interactive element must supply an
 * accessible name, such as "Upstream home" for a home link.
 */
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
