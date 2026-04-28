# Spec: Haravan Social Login

## Requirement: Login Button

The Frappe login page shall display a social login option named `Haravan Account` when the `haravan_account` Social Login Key is enabled and has valid client credentials.

### Scenario: Provider is configured

- Given a Social Login Key named `haravan_account`
- And `enable_social_login` is true
- And `client_id` and `client_secret` are present
- When a user opens `/login`
- Then a `Haravan Account` login option is shown

## Requirement: OAuth Redirect

The OAuth authorize request shall use an exact redirect URI registered in Haravan Partner Dashboard.

### Scenario: Redirect URI is valid

- Given Haravan Partner Dashboard contains the callback URL
- When Frappe redirects to `accounts.haravan.com/connect/authorize`
- Then Haravan accepts the request and shows the login/consent flow

### Scenario: Redirect URI is invalid

- Given Haravan Partner Dashboard does not contain the callback URL
- When Frappe redirects to `accounts.haravan.com/connect/authorize`
- Then Haravan returns `invalid_request Invalid redirect_uri`

## Requirement: User Login

The callback shall create a Frappe session for the authenticated Haravan user.

### Scenario: Userinfo has required fields

- Given Haravan userinfo contains `email`, `sub` or `userid`, and `orgid`
- When the callback receives a valid authorization code
- Then Frappe logs in the matching or newly created user

## Requirement: Identity Persistence

The callback shall store Haravan identity in `Haravan Account Link`.

### Scenario: First login

- Given no link exists for the Haravan org/user pair
- When login completes
- Then a new `Haravan Account Link` is inserted

### Scenario: Repeat login

- Given a link exists for the Haravan org/user pair
- When login completes again
- Then the same link is updated with latest profile and `last_login`
