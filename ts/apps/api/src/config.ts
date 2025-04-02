import { z } from "zod";

// TODO: find pattern where we get
//  - nicely nested config objects
//  - and type safety for env vars
//  - and nice error types all in one place

// TODO (service-setup): implement your service config via env vars here!
// Raw environment schema
const envSchema = z.object({
  // NOTE: all services will probably require a basePath when proxied behind
  //  an Application Load Balancer in ECS.
  // TODO: ensure path is form of /<basePath>
  BASE_PATH: z.string().optional(),

  // TODO (service-setup): replace this with an unused port field for use within development
  //  environments. This pretty much gets set to 3000 in all production and
  //  staging environments, for all services.
  PORT: z.coerce.number().default(3001),

  ENV: z
    .enum(["development", "staging", "production", "test"])
    .default("development"),

  // Logging configuration
  LOG_LEVEL: z
    .enum(["fatal", "error", "warn", "info", "debug", "trace"])
    .default("info"),
});

// Parse env vars with better error handling
const parseEnv = () => {
  const result = envSchema.safeParse(process.env);

  if (!result.success) {
    const missing = result.error.issues
      .filter((i) => i.code === "invalid_type" && i.received === "undefined")
      .map((i) => i.path.join("."));

    if (missing.length) {
      const MAX_TO_SHOW = 5;
      const truncated =
        missing.length > MAX_TO_SHOW ? missing.slice(0, MAX_TO_SHOW) : missing;

      const message = `Missing environment variables: ${truncated.join(", ")}${
        missing.length > MAX_TO_SHOW
          ? `, and ${missing.length - MAX_TO_SHOW} more`
          : ""
      }.\nMake sure these are set in your .env file or environment.`;

      throw new Error(message);
    }
    throw result.error;
  }

  return result.data;
};

const env = parseEnv();

// TODO (service-setup): implement your service config at runtime here!
// Structured config for nicely mapping env vars to config objects
export const config = {
  isEcsEnvironment: !!process.env.AWS_CONTAINER_CREDENTIALS_RELATIVE_URI,
  server: {
    port: env.PORT,
    env: env.ENV,
    basePath: env.BASE_PATH,
  },
  log: {
    level: env.LOG_LEVEL,
  },
} as const;

export type Config = typeof config;
