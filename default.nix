let
  inherit (import <nixpkgs> {}) pkgs;

in pkgs.python27Packages.buildPythonPackage {
  name = "scan2pdf"; # TODO rename to avoid conflict with gscan2pdf?
  src = ./.;
  buildInputs = with pkgs; [
    imagemagick
    libtiff
  ];
  meta = {
    license = pkgs.stdenv.lib.licenses.gpl3; # TODO check dependencies
  };
  doCheck = false;
}
