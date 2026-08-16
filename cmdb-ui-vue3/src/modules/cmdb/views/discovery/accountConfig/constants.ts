/** Default config fields for each HTTP account provider. */
export const defaultConfig: Record<string, Record<string, string>> = {
  public: {
    key: '',
    secret: '',
  },
  vcenter: {
    host: '',
    account: '',
    password: '',
  },
}
