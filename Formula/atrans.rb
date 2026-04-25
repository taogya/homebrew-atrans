class Atrans < Formula
  desc "CLI translation tool powered by Apple Translation API"
  homepage "https://github.com/taogya/homebrew-atrans"
  head "https://github.com/taogya/homebrew-atrans.git", branch: "main"
  license "BSD-3-Clause"

  depends_on xcode: ["26.0", :build]
  depends_on :macos => :tahoe # macOS 26

  def install
    system "swift", "build",
           "-c", "release",
           "--disable-sandbox"
    bin.install ".build/release/atrans"
  end

  def caveats
    <<~EOS
      After installation, refresh your shell's hash table:

        hash -r

      Translation language packs are required. Download them in advance:

        System Settings > General > Translation Languages
    EOS
  end

  test do
    assert_match "atrans", shell_output("#{bin}/atrans --version")
  end
end