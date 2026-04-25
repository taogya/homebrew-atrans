class Atrans < Formula
  desc "CLI translation tool powered by Apple Translation API"
  homepage "https://github.com/taogya/homebrew-atrans"
  url "https://github.com/taogya/homebrew-atrans/archive/refs/tags/v2.0.0.tar.gz"
  sha256 "a94b9d99e0f09d64c1db65e86fc17403248d446b7ca486c39589e266e8a2251b"
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
    assert_match "atrans 2.0.0", shell_output("#{bin}/atrans --version")
  end
end