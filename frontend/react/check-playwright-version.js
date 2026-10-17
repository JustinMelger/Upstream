import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const manifest = JSON.parse(
  readFileSync(new URL("./package.json", import.meta.url), "utf8"),
);
const lock = JSON.parse(
  readFileSync(new URL("./package-lock.json", import.meta.url), "utf8"),
);
const dockerfile = readFileSync(
  new URL("./Dockerfile.visual", import.meta.url),
  "utf8",
);
const version = manifest.devDependencies["@playwright/test"];
const image = dockerfile.match(
  /^FROM mcr\.microsoft\.com\/playwright:v(\d+\.\d+\.\d+)-noble@sha256:[a-f0-9]{64}\s*$/m,
);

assert.match(
  version,
  /^\d+\.\d+\.\d+$/,
  "Pin @playwright/test to an exact version.",
);
assert.ok(
  image,
  "Dockerfile.visual must pin the Playwright noble image by version and digest.",
);

for (const name of ["@playwright/test", "playwright", "playwright-core"]) {
  assert.equal(
    lock.packages[`node_modules/${name}`]?.version,
    version,
    `package-lock.json: ${name} must match @playwright/test ${version}.`,
  );
}

assert.equal(
  lock.packages[""].devDependencies["@playwright/test"],
  version,
  "The lockfile root must match the exact Playwright pin.",
);
assert.equal(
  require("@playwright/test/package.json").version,
  version,
  "Installed Playwright differs from the pin; run npm ci.",
);
assert.equal(
  image[1],
  version,
  `Dockerfile.visual must use Playwright v${version}-noble and its matching digest.`,
);
console.log(
  `Playwright ${version}: package, lockfile, installation and Docker image versions match.`,
);
