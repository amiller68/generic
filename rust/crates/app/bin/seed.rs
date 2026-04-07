use generic_rust_app::database::models::{User, UserPatch, Widget, WidgetPatch};
use generic_rust_app::database::Database;

struct UserSeed {
    email: &'static str,
    name: &'static str,
    is_admin: bool,
}

struct WidgetSeed {
    name: &'static str,
    description: &'static str,
    status: &'static str,
}

const USERS: &[UserSeed] = &[UserSeed {
    email: "al@krondor.org",
    name: "Al",
    is_admin: true,
}];

const WIDGETS: &[WidgetSeed] = &[
    WidgetSeed {
        name: "Homepage Banner",
        description: "Main banner displayed on the homepage",
        status: "active",
    },
    WidgetSeed {
        name: "Dashboard Stats",
        description: "Statistics widget for the user dashboard",
        status: "active",
    },
    WidgetSeed {
        name: "Newsletter Signup",
        description: "Email capture form for newsletter",
        status: "draft",
    },
    WidgetSeed {
        name: "Social Media Feed",
        description: "Displays latest social media posts",
        status: "draft",
    },
    WidgetSeed {
        name: "Legacy Footer",
        description: "Old footer widget - to be removed",
        status: "archived",
    },
];

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt::init();

    let database_url =
        std::env::var("SQLITE_DATABASE_URL").unwrap_or_else(|_| "sqlite://data/app.db".to_string());

    let url = url::Url::parse(&database_url).expect("invalid SQLITE_DATABASE_URL");
    let db = Database::connect(&url)
        .await
        .expect("failed to connect to database");

    if let Err(e) = run(&db).await {
        tracing::error!("seeding failed: {e}");
        std::process::exit(1);
    }
    tracing::info!("seeding complete");
}

async fn run(db: &Database) -> anyhow::Result<()> {
    for seed in USERS {
        let patch = UserPatch {
            name: Some(seed.name.into()),
            is_admin: Some(seed.is_admin),
            ..Default::default()
        };

        match User::find_by_email(seed.email, db).await? {
            Some(existing) => {
                if existing.name() != seed.name || existing.is_admin() != seed.is_admin {
                    tracing::info!(email = seed.email, "updating user");
                    existing.patch(patch, db).await?;
                } else {
                    tracing::info!(email = seed.email, "user unchanged, skipping");
                }
            }
            None => {
                tracing::info!(email = seed.email, "creating user");
                let user = User::create(seed.email, seed.name, db).await?;
                user.patch(patch, db).await?;
            }
        }
    }

    for seed in WIDGETS {
        match Widget::find_by_name(seed.name, db).await? {
            Some(existing) => {
                tracing::info!(name = seed.name, "updating widget");
                let patch = WidgetPatch {
                    description: Some(seed.description.into()),
                    status: Some(seed.status.into()),
                    ..Default::default()
                };
                existing.patch(patch, db).await?;
            }
            None => {
                tracing::info!(name = seed.name, "creating widget");
                Widget::create(seed.name, seed.description, db).await?;
            }
        }
    }

    Ok(())
}
